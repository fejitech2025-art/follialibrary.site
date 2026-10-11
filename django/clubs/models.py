from django.conf import settings
from django.db import models


class BookClub(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_book_clubs")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    avatar = models.FileField(upload_to="book-clubs/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else ""

    @property
    def member_count(self):
        return self.memberships.count()

    def __str__(self):
        return self.name


class BookClubMembership(models.Model):
    ROLE_CHOICES = [("owner", "Owner"), ("admin", "Admin"), ("member", "Member")]
    club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_club_memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]
        constraints = [models.UniqueConstraint(fields=["club", "user"], name="unique_book_club_member")]


class BookClubResource(models.Model):
    club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name="club_resources")
    resource = models.ForeignKey("library.Resource", on_delete=models.CASCADE, related_name="club_links")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="club_resources_added")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [models.UniqueConstraint(fields=["club", "resource"], name="unique_resource_per_club")]


class BookClubMessage(models.Model):
    club = models.ForeignKey(BookClub, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_club_messages")
    content = models.CharField(max_length=3000)
    reply_to = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
