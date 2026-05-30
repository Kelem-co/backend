import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from messaging.access import user_can_access_thread
from messaging.models import ChatThread


class ThreadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.group_name = f"chat_thread_{self.thread_id}"

        thread = await self._get_thread()
        if thread is None:
            await self.close(code=4404)
            return

        if not await self._can_access(thread):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        del close_code
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        del text_data, bytes_data

    async def chat_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _get_thread(self):
        try:
            return ChatThread.objects.select_related(
                "parent__user",
                "teacher__user",
            ).get(id=self.thread_id)
        except ChatThread.DoesNotExist:
            return None

    @database_sync_to_async
    def _can_access(self, thread):
        return user_can_access_thread(self.scope["user"], thread)
