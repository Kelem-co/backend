import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from communications.models import ChatRoom, Message
from teachers.models import Teacher
from students.models import Parent


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope['user']

        # Reject connection if user is not authenticated
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return

        # Check authorization
        is_authorized = await self.check_authorization()
        if not is_authorized:
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Mark messages as read when connecting
        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json.get('content', '')

        if not content:
            return

        # Save message to database
        message = await self.save_message(content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': str(message.id),
                'room': str(self.room_id),
                'sender': str(self.user.id),
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'room': event['room'],
            'sender': event['sender'],
            'content': event['content'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def check_authorization(self):
        try:
            room = ChatRoom.objects.select_related('teacher__user', 'parent__user').get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return False

        if self.user.role == "TEACHER":
            return room.teacher.user == self.user
        elif self.user.role == "PARENT":
            return room.parent.user == self.user
            
        return False

    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(id=self.room_id)
        return Message.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        
    @database_sync_to_async
    def mark_messages_as_read(self):
        # Mark messages sent by the other party as read
        Message.objects.filter(
            room_id=self.room_id,
            is_read=False
        ).exclude(
            sender=self.user
        ).update(is_read=True)
