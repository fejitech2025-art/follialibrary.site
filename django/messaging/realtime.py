from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_user_event(user_id, payload):
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)(f"dm_user_{user_id}", {"type": "user.event", "payload": payload})
    except Exception:
        # Persisted messages must not fail because live delivery is unavailable.
        return

