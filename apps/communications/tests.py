import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from communications.models import ChatRoom, Message, BroadcastLog
from students.tests.factories import ParentFactory, StudentFactory, ParentStudentLinkFactory
from teachers.tests.factories import TeacherFactory, TeacherSubjectAssignmentFactory
from academics.tests.factories import SectionFactory
from communications.tasks import send_broadcast_messages

pytestmark = pytest.mark.django_db

def test_chatroom_creation():
    teacher = TeacherFactory()
    parent = ParentFactory()
    
    room = ChatRoom.objects.create(teacher=teacher, parent=parent)
    
    assert ChatRoom.objects.count() == 1
    assert room.teacher == teacher
    assert room.parent == parent
    assert str(room) == f"Chat: {teacher} - {parent}"

def test_message_creation():
    teacher = TeacherFactory()
    parent = ParentFactory()
    room = ChatRoom.objects.create(teacher=teacher, parent=parent)
    
    msg = Message.objects.create(
        room=room,
        sender=teacher.user,
        content="Hello Parent!"
    )
    
    assert Message.objects.count() == 1
    assert msg.room == room
    assert msg.sender == teacher.user
    assert msg.content == "Hello Parent!"
    assert msg.is_read is False

def test_broadcast_task_creates_messages():
    teacher = TeacherFactory()
    parent1 = ParentFactory()
    parent2 = ParentFactory()
    
    send_broadcast_messages(
        teacher_id=teacher.id,
        parent_ids=[parent1.id, parent2.id],
        content="School will be closed tomorrow."
    )
    
    assert ChatRoom.objects.count() == 2
    assert Message.objects.count() == 2
    assert BroadcastLog.objects.count() == 1
    
    log = BroadcastLog.objects.first()
    assert log.teacher == teacher
    assert log.recipient_count == 2
    assert log.message_body == "School will be closed tomorrow."

def test_broadcast_api_view_unauthorized(client):
    """Test that only teachers can broadcast messages."""
    parent = ParentFactory()
    client = APIClient()
    client.force_authenticate(user=parent.user)
    
    url = reverse("api:chat-broadcast")
    response = client.post(url, {"parent_ids": [parent.id], "content": "Test"})
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_broadcast_api_view_authorized_but_invalid_parent(client):
    """Test teacher cannot broadcast to a parent whose child they don't teach."""
    teacher = TeacherFactory()
    parent = ParentFactory()
    
    client = APIClient()
    client.force_authenticate(user=teacher.user)
    
    url = reverse("api:chat-broadcast")
    response = client.post(url, {"parent_ids": [parent.id], "content": "Test"})
    
    # Validation should fail because the teacher does not teach this parent's child
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "None of the specified parents are linked to your students" in response.data["detail"]

def test_broadcast_api_view_authorized_valid_parent(client):
    """Test teacher can broadcast to a parent if they teach their child."""
    teacher = TeacherFactory()
    parent = ParentFactory()
    section = SectionFactory()
    student = StudentFactory(current_section=section)
    ParentStudentLinkFactory(student=student, parent=parent)
    TeacherSubjectAssignmentFactory(teacher=teacher, section=section)
    
    client = APIClient()
    client.force_authenticate(user=teacher.user)
    
    url = reverse("api:chat-broadcast")
    response = client.post(url, {"parent_ids": [parent.id], "content": "Test message"})
    
    assert response.status_code == status.HTTP_202_ACCEPTED
