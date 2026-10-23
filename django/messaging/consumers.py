from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation, UserBlock


class DirectMessageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user_id = user.pk
        self.group_name = f"dm_user_{self.user_id}"
        self.typing_to = {}
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        for conversation_id, recipient_id in list(getattr(self, "typing_to", {}).items()):
            await self.channel_layer.group_send(
                f"dm_user_{recipient_id}",
                {"type": "user.event", "payload": {"type": "typing", "conversation_id": conversation_id,
                 "user_id": self.user_id, "active": False}},
            )
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "typing":
            return
        try:
            conversation_id = int(content.get("conversation_id"))
        except (TypeError, ValueError):
            return
        recipient_id = await self.typing_recipient(conversation_id)
        if not recipient_id:
            return
        active = bool(content.get("active"))
        if active:
            self.typing_to[conversation_id] = recipient_id
        else:
            self.typing_to.pop(conversation_id, None)
        await self.channel_layer.group_send(
            f"dm_user_{recipient_id}",
            {"type": "user.event", "payload": {"type": "typing", "conversation_id": conversation_id,
             "user_id": self.user_id, "active": active}},
        )

    async def user_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def typing_recipient(self, conversation_id):
        conversation = Conversation.objects.filter(pk=conversation_id).first()
        if not conversation or self.user_id not in (conversation.user_one_id, conversation.user_two_id):
            return None
        other_id = conversation.user_two_id if self.user_id == conversation.user_one_id else conversation.user_one_id
        if UserBlock.objects.filter(
            blocker_id__in=[self.user_id, other_id], blocked_id__in=[self.user_id, other_id]
        ).exists():
            return None
        return other_id

