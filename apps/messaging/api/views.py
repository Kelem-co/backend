import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from messaging.access import thread_scope_filter_for_user
from messaging.access import user_can_access_thread
from messaging.models import ChatThread
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .serializers import ChatMessageSerializer
from .serializers import ChatThreadSerializer
from .serializers import MarkReadSerializer
from .serializers import ResolveThreadSerializer


def _json_safe(data):
    return json.loads(JSONRenderer().render(data))


class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        qs = ChatThread.objects.select_related(
            "parent__user",
            "teacher__user",
            "student",
            "organization",
            "branch",
        )

        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        return qs.filter(thread_scope_filter_for_user(self.request.user)).distinct()

    @action(detail=False, methods=["get"], url_path="resolve")
    def resolve(self, request, *args, **kwargs):
        del args, kwargs
        params = ResolveThreadSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        queryset = self.get_queryset().filter(
            student_id=params.validated_data["student"],
        )
        teacher_id = params.validated_data.get("teacher")
        parent_id = params.validated_data.get("parent")

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        thread = queryset.first()
        if thread is None:
            return Response({"thread": None, "messages": []}, status=status.HTTP_200_OK)

        messages = thread.messages.select_related("sender", "attachment").all()
        return Response(
            {
                "thread": ChatThreadSerializer(
                    thread,
                    context={"request": request},
                ).data,
                "messages": ChatMessageSerializer(
                    messages,
                    many=True,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, *args, **kwargs):
        del args, kwargs
        thread = self.get_object()
        if not user_can_access_thread(request.user, thread):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        if request.method == "GET":
            queryset = thread.messages.select_related("sender", "attachment").all()
            serializer = ChatMessageSerializer(
                queryset,
                many=True,
                context={"request": request},
            )
            return Response(serializer.data)

        serializer = ChatMessageSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save(thread=thread, sender=request.user)

        message_data = ChatMessageSerializer(
            message,
            context={"request": request},
        ).data
        payload = {
            "event": "message.created",
            "thread_id": str(thread.id),
            "message": _json_safe(message_data),
        }
        async_to_sync(get_channel_layer().group_send)(
            f"chat_thread_{thread.id}",
            {"type": "chat.event", "payload": payload},
        )
        return Response(message_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, *args, **kwargs):
        del args, kwargs
        thread = self.get_object()
        serializer = MarkReadSerializer(
            data=request.data,
            context={"request": request, "thread": thread},
        )
        serializer.is_valid(raise_exception=True)
        reads = serializer.save()

        if reads:
            payload = {
                "event": "message.read",
                "thread_id": str(thread.id),
                "reader_id": str(request.user.id),
                "count": len(reads),
            }
            async_to_sync(get_channel_layer().group_send)(
                f"chat_thread_{thread.id}",
                {"type": "chat.event", "payload": payload},
            )
        return Response({"count": len(reads)}, status=status.HTTP_200_OK)
