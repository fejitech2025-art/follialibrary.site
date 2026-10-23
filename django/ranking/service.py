from datetime import datetime, time

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from channels.layers import get_channel_layer
from django.core.cache import cache

from .models import RankEvent

User = get_user_model()


def _clear_rank_cache():
    cache.delete_many(["follia:rank-map:overall", "follia:rank-map:daily",
                       "follia:rank-leaderboard:overall", "follia:rank-leaderboard:daily"])


def _points(kind):
    return max(0, int(getattr(settings, "RANKING_WEIGHTS", {}).get(kind, 0)))


def record_event(user, kind, activity_key, *, actor=None, reactivate=False):
    """Create an idempotent, server-authored rank event."""
    points = _points(kind)
    if not user or not points:
        return None
    event, created = RankEvent.objects.get_or_create(
        activity_key=activity_key,
        defaults={"user": user, "actor": actor, "kind": kind, "points": points},
    )
    changed = created
    if not created and reactivate and not event.active:
        event.active = True
        event.save(update_fields=["active"])
        changed = True
    if changed:
        _clear_rank_cache()
        transaction.on_commit(broadcast_ranking_update)
    return event


def deactivate_event(activity_key):
    changed = RankEvent.objects.filter(activity_key=activity_key, active=True).update(active=False)
    if changed:
        _clear_rank_cache()
        transaction.on_commit(broadcast_ranking_update)


def award_comment(comment, post_author, source="post"):
    actor = comment.user
    day_start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    daily_limit = max(0, int(getattr(settings, "RANKING_DAILY_COMMENT_LIMIT", 10)))
    if actor.pk != post_author.pk and len(comment.content.strip()) >= 12:
        already_awarded = RankEvent.objects.filter(
            user=actor,
            kind="comment_written",
            created_at__gte=day_start,
        ).count()
        if already_awarded < daily_limit:
            record_event(actor, "comment_written", f"{source}-comment-written:{comment.pk}", actor=actor)
        already_received = RankEvent.objects.filter(
            user=post_author,
            actor=actor,
            kind="comment_received",
            created_at__gte=day_start,
        ).count()
        if already_received < 3:
            record_event(post_author, "comment_received", f"{source}-comment-received:{comment.pk}", actor=actor)


def award_received_like(recipient, actor, activity_key):
    day_start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    limit = max(0, int(getattr(settings, "RANKING_DAILY_RECEIVED_LIKE_LIMIT", 20)))
    already_awarded = RankEvent.objects.filter(
        user=recipient,
        kind="post_like_received",
        created_at__gte=day_start,
    ).count()
    if already_awarded < limit:
        return record_event(recipient, "post_like_received", activity_key, actor=actor, reactivate=True)
    return None


def award_post(post):
    day_start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    limit = max(0, int(getattr(settings, "RANKING_DAILY_POST_LIMIT", 10)))
    already_awarded = RankEvent.objects.filter(user=post.author, kind="post_published",
                                                created_at__gte=day_start).count()
    if already_awarded >= limit:
        return
    record_event(post.author, "post_published", f"post-published:{post.pk}", actor=post.author)
    if post.media or post.media_items.exists():
        record_event(post.author, "media_published", f"post-media:{post.pk}", actor=post.author)


def award_resource(resource):
    day_start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    limit = max(0, int(getattr(settings, "RANKING_DAILY_RESOURCE_LIMIT", 5)))
    already_awarded = RankEvent.objects.filter(user=resource.author, kind="resource_published",
                                                created_at__gte=day_start).count()
    if already_awarded < limit:
        record_event(resource.author, "resource_published", f"resource-published:{resource.pk}", actor=resource.author)


def undo_post(post):
    deactivate_event(f"post-published:{post.pk}")
    deactivate_event(f"post-media:{post.pk}")
    for like in post.likes.select_related("user"):
        deactivate_event(f"post-like:{like.user_id}:{post.pk}")
    for comment in post.comments.select_related("user"):
        deactivate_event(f"post-comment-written:{comment.pk}")
        deactivate_event(f"post-comment-received:{comment.pk}")


def undo_resource(resource):
    deactivate_event(f"resource-published:{resource.pk}")
    for like in resource.likes.select_related("user"):
        deactivate_event(f"resource-like:{like.user_id}:{resource.pk}")
    for comment in resource.comments.select_related("user"):
        deactivate_event(f"resource-comment-written:{comment.pk}")
        deactivate_event(f"resource-comment-received:{comment.pk}")


def _score_query(period):
    query = RankEvent.objects.filter(active=True)
    if period == "daily":
        start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
        query = query.filter(active_since__gte=start)
    return query.values("user_id").annotate(score=Sum("points")).order_by("-score", "user_id")


def rank_for_user(user_id, period="overall"):
    if not user_id:
        return {"rank": None, "score": 0}
    rows = list(_score_query(period))
    for position, row in enumerate(rows, start=1):
        if row["user_id"] == user_id:
            return {"rank": position, "score": row["score"] or 0}
    return {"rank": None, "score": 0}


def rank_map(period="overall"):
    key = f"follia:rank-map:{period}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = {
        row["user_id"]: {"rank": position, "score": row["score"] or 0}
        for position, row in enumerate(_score_query(period), start=1)
    }
    cache.set(key, result, timeout=15)
    return result


def leaderboard(period="overall", limit=100):
    key = f"follia:rank-leaderboard:{period}"
    rows = cache.get(key)
    if rows is None:
        rows = list(_score_query(period)[:limit])
        cache.set(key, rows, timeout=10)
    users = User.objects.filter(pk__in=[row["user_id"] for row in rows]).select_related("profile")
    by_id = {user.pk: user for user in users}
    result = []
    for position, row in enumerate(rows, start=1):
        user = by_id.get(row["user_id"])
        if not user:
            continue
        profile = getattr(user, "profile", None)
        result.append({
            "rank": position,
            "score": row["score"] or 0,
            "user_id": user.pk,
            "id": user.pk,
            "username": profile.username if profile else user.username,
            "display_name": (profile.display_name or profile.username) if profile else user.get_full_name() or user.username,
            "avatar_url": profile.avatar_url if profile else "",
        })
    return result


def broadcast_ranking_update():
    _clear_rank_cache()
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)("ranks", {"type": "ranking.changed"})
    except Exception:
        # Rank writes must succeed even if the optional realtime layer is down.
        return

