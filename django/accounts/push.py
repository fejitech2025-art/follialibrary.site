import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def notification_message(notification):
    actor = getattr(getattr(notification.actor, "profile", None), "display_name", "")
    actor = actor or getattr(getattr(notification.actor, "profile", None), "username", "") or "Someone"
    messages = {
        "follow": f"{actor} followed you.",
        "like": f"{actor} liked your post.",
        "comment": f"{actor} commented on your content.",
        "comment_reply": f"{actor} replied to your comment.",
        "comment_like": f"{actor} liked your comment.",
        "book_club_join": f"{actor} joined your Book Club.",
        "book_club_reply": f"{actor} replied in your Book Club.",
        "book_club_admin": f"{actor} updated your Book Club role.",
    }
    return messages.get(notification.type, "You have a new Follia Library notification.")


def send_notification_push(notification_id):
    if not (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT):
        return

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.exception("Web push is configured, but pywebpush is not installed")
        return

    from .models import Notification, PushSubscription

    notification = Notification.objects.select_related("actor__profile").filter(pk=notification_id).first()
    if not notification:
        return

    target_url = f"{settings.FRONTEND_URL}/notifications"
    if notification.post_id and notification.comment_id:
        target_url = f"{settings.FRONTEND_URL}/post/{notification.post_id}?comment={notification.comment_id}"
    elif notification.resource_id and notification.comment_id:
        target_url = f"{settings.FRONTEND_URL}/resource/{notification.resource_id}?comment={notification.comment_id}"
    payload = json.dumps({
        "id": notification.pk,
        "title": "Follia Library",
        "body": notification_message(notification),
        "url": target_url,
    })

    subscriptions = PushSubscription.objects.filter(user_id=notification.recipient_id)
    for subscription in subscriptions.iterator():
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                ttl=60,
            )
        except WebPushException as error:
            if error.response is not None and error.response.status_code in (404, 410):
                subscription.delete()
            else:
                logger.warning("Web push delivery failed for subscription %s: %s", subscription.pk, error)
        except Exception:
            logger.exception("Web push delivery failed for subscription %s", subscription.pk)
