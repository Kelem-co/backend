from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from communications.models import ChatRoom, Message
from communications.serializers import MessageSerializer, BroadcastSerializer
from communications.tasks import send_broadcast_messages
from students.models import Parent, Student, ParentStudentLink
from teachers.models import Teacher, TeacherSubjectAssignment, HomeroomAssignment


class MessagePagination(CursorPagination):
    page_size = 50
    ordering = "-created_at"


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve messages for a specific chat room.
    """
    serializer_class = MessageSerializer
    pagination_class = MessagePagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs.get("room_pk")
        user = self.request.user
        
        room = get_object_or_404(ChatRoom, pk=room_id)
        
        # Check authorization
        if user.role == "TEACHER":
            if room.teacher.user != user:
                raise PermissionDenied("You are not a participant in this room.")
        elif user.role == "PARENT":
            if room.parent.user != user:
                raise PermissionDenied("You are not a participant in this room.")
        else:
            raise PermissionDenied("You do not have permission to view chat rooms.")
            
        return Message.objects.filter(room=room)


class BroadcastView(APIView):
    """
    API View for teachers to broadcast a message to multiple parents.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != "TEACHER":
            return Response(
                {"detail": "Only teachers can broadcast messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return Response(
                {"detail": "Teacher profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BroadcastSerializer(data=request.data)
        if serializer.is_valid():
            parent_ids = serializer.validated_data["parent_ids"]
            content = serializer.validated_data["content"]
            
            # Validate that the teacher actually teaches the students of these parents
            valid_parent_ids = []
            
            # Get all sections the teacher is assigned to (subject or homeroom)
            assigned_sections = set(
                TeacherSubjectAssignment.objects.filter(teacher=teacher)
                .values_list("section_id", flat=True)
            )
            assigned_sections.update(
                HomeroomAssignment.objects.filter(teacher=teacher)
                .values_list("section_id", flat=True)
            )
            
            for parent_id in parent_ids:
                try:
                    parent = Parent.objects.get(pk=parent_id)
                except Parent.DoesNotExist:
                    continue
                    
                # Get the parent's students
                parent_students = [link.student for link in ParentStudentLink.objects.filter(parent=parent)]
                
                # Check if any of the parent's students are in the teacher's sections
                is_authorized = False
                for student in parent_students:
                    if student.current_section_id in assigned_sections:
                        is_authorized = True
                        break
                        
                if is_authorized:
                    valid_parent_ids.append(parent_id)
            
            if not valid_parent_ids:
                return Response(
                    {"detail": "None of the specified parents are linked to your students."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Trigger Celery task
            send_broadcast_messages.delay(
                teacher_id=teacher.id,
                parent_ids=valid_parent_ids,
                content=content
            )
            
            return Response(
                {"detail": "Broadcast message queued successfully."},
                status=status.HTTP_202_ACCEPTED
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
