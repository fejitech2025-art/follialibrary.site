from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RankingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        await self.channel_layer.group_add("ranks", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("ranks", self.channel_name)

    async def receive_json(self, content, **kwargs):
        return

    async def ranking_changed(self, event):
        await self.send_json({"type": "ranking_changed"})

