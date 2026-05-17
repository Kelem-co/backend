from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from communications.models import ChatRoom
from communications.models import Message
from communications.models import BroadcastLog
from students.models import Parent
from teachers.models import Teacher


@shared_task
def send_broadcast_messages(teacher_id, parent_ids, content):
    """
    Sends a broadcast message from a teacher to multiple parents.
    Creates 1-to-1 ChatRoom instances if they don't exist, saves the messages,
    and broadcasts the messages via WebSocket.
    """
    teacher = Teacher.objects.get(id=teacher_id)
    parents = Parent.objects.filter(id__in=parent_ids)
    
    channel_layer = get_channel_layer()
    
    successful_count = 0
    for parent in parents:
        room, _ = ChatRoom.objects.get_or_create(teacher=teacher, parent=parent)
        
        message = Message.objects.create(
            room=room,
            sender=teacher.user,
            content=content,
        )
        
        successful_count += 1
        
        # Broadcast via WebSocket if the room channel group exists
        if channel_layer is not None:
            group_name = f"chat_{room.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "chat_message",
                    "id": str(message.id),
                    "room": str(room.id),
                    "sender": str(message.sender.id),
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
            )
            
    BroadcastLog.objects.create(
        teacher=teacher,
        message_body=content,
        recipient_count=successful_count,
    )
