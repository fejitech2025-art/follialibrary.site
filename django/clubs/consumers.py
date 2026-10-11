from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import BookClubMembership


class ClubChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.club_id = self.scope["url_route"]["kwargs"]["club_id"]
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not await self.is_member(user.pk, self.club_id):
            await self.close(code=4403)
            return
        self.group_name = f"club_{self.club_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Writes use the authenticated HTTP API; the socket only delivers live club events.
        return

    async def chat_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def is_member(self, user_id, club_id):
        return BookClubMembership.objects.filter(user_id=user_id, club_id=club_id).exists()
