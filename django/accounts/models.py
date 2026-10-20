import hashlib

from django.conf import settings
from django.db import models
from django.db import transaction

from config.storage_backends import storage_file_url


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    username = models.SlugField(max_length=30, unique=True)
    display_name = models.CharField(max_length=80, blank=True)
    avatar = models.FileField(upload_to="avatars/",blank=True,)
    bio = models.CharField(max_length=280, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def avatar_url(self):
        return storage_file_url(self.avatar)

    def __str__(self):
        return f"@{self.username}"


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_edges")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_edges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_user_follow"),
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")), name="no_self_follow"),
        ]
        ordering = ["-created_at"]


class Notification(models.Model):
    TYPE_CHOICES = [
        ("follow", "Follow"),
        ("like", "Like"),
        ("comment", "Comment"),
        ("comment_reply", "Comment reply"),
        ("book_club_join", "Book Club activity"),
        ("book_club_reply", "Book Club reply"),
        ("book_club_admin", "Book Club role"),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_notifications")
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    post_id = models.PositiveBigIntegerField(null=True, blank=True)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True)
    book_club_id = models.PositiveBigIntegerField(null=True, blank=True)
    event_key = models.CharField(max_length=150, null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_key"],
                name="unique_notification_event_per_recipient",
            ),
        ]


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=2048)
    endpoint_hash = models.CharField(max_length=64, unique=True, editable=False)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        self.endpoint_hash = hashlib.sha256(self.endpoint.encode("utf-8")).hexdigest()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"endpoint_hash"}
        super().save(*args, **kwargs)


def notify(
    recipient,
    actor,
    kind,
    *,
    post_id=None,
    resource_id=None,
    book_club_id=None,
    event_key=None,
):
    if not recipient or not actor or recipient.pk == actor.pk:
        return None
    defaults = {
        "actor": actor,
        "type": kind,
        "post_id": post_id,
        "resource_id": resource_id,
        "book_club_id": book_club_id,
    }
    if event_key:
        notification, created = Notification.objects.get_or_create(
            recipient=recipient,
            event_key=event_key,
            defaults=defaults,
        )
    else:
        notification = Notification.objects.create(
            recipient=recipient,
            event_key=None,
            **defaults,
        )
        created = True
    if created:
        transaction.on_commit(
            lambda notification_id=notification.pk: _dispatch_push(notification_id)
        )
    return notification


def _dispatch_push(notification_id):
    from .push import send_notification_push

    send_notification_push(notification_id)
