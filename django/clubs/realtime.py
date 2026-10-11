from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_club_event(club_id, payload):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f"club_{club_id}", {"type": "chat.event", "payload": payload})


def message_payload(message):
    profile = getattr(message.sender, "profile", None)
    return {
        "id": message.pk,
        "club_id": message.club_id,
        "sender_id": message.sender_id,
        "content": message.content,
        "reply_to": message.reply_to_id,
        "reply_to_id": message.reply_to_id,
        "is_pinned": message.is_pinned,
        "created_at": message.created_at.isoformat(),
        "profiles": {
            "id": message.sender_id,
            "username": profile.username if profile else message.sender.username,
            "display_name": profile.display_name if profile else message.sender.get_full_name(),
            "avatar_url": profile.avatar_url if profile else "",
        },
    }
