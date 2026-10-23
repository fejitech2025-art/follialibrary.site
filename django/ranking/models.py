from django.conf import settings
from django.db import models
from django.utils import timezone


class RankEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rank_events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rank_actions",
    )
    activity_key = models.CharField(max_length=190, unique=True)
    kind = models.CharField(max_length=32)
    points = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active_since = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user", "active", "active_since"], name="rank_user_period_idx"),
            models.Index(fields=["kind", "active_since"], name="rank_kind_period_idx"),
            models.Index(fields=["user", "kind", "created_at"], name="rank_daily_cap_idx"),
            models.Index(fields=["user", "actor", "kind", "created_at"], name="rank_actor_daily_idx"),
        ]
        ordering = ["-created_at"]

