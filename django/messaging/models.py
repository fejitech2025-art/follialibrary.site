import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):
    user_one = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dm_conversations_one")
    user_two = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dm_conversations_two")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_one", "user_two"], name="unique_direct_conversation"),
            models.CheckConstraint(condition=Q(user_one__lt=F("user_two")), name="ordered_direct_participants"),
        ]
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["-updated_at", "-id"], name="dm_recent_conversation_idx")]


class DirectMessage(models.Model):
    TYPE_CHOICES = [("text", "Text"), ("voice", "Voice note"), ("sticker", "Sticker"), ("post_share", "Shared post")]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="direct_messages")
    client_id = models.UUIDField(default=uuid.uuid4)
    message_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="text")
    body = models.CharField(max_length=3000, blank=True)
    attachment = models.FileField(upload_to="direct-messages/", blank=True)
    duration_seconds = models.PositiveSmallIntegerField(null=True, blank=True)
    shared_post = models.ForeignKey("social.Post", null=True, blank=True, on_delete=models.SET_NULL, related_name="shared_in_messages")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["conversation", "sender", "client_id"], name="unique_dm_client_message")]
        indexes = [models.Index(fields=["conversation", "-created_at", "-id"], name="dm_history_page_idx")]


class UserBlock(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_made")
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_user_block")]
        indexes = [models.Index(fields=["blocker", "blocked"], name="dm_block_pair_idx")]


class MessageReport(models.Model):
    REASONS = [("spam", "Spam"), ("harassment", "Harassment"), ("inappropriate", "Inappropriate content"), ("other", "Other")]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_reports")
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=24, choices=REASONS, default="other")
    description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["reporter", "message"], name="unique_message_report")]
        ordering = ["-created_at"]

