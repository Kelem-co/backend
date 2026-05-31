import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Prefetch
from messaging.access import thread_scope_filter_for_user
from messaging.access import user_can_access_thread
from messaging.models import ChatMessage
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


def _json_safe(data):
    return json.loads(JSONRenderer().render(data))


class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        message_qs = ChatMessage.objects.select_related("sender", "attachment")
        qs = ChatThread.objects.select_related(
            "parent__user",
            "teacher__user",
            "student",
            "organization",
            "branch",
        ).prefetch_related(Prefetch("messages", queryset=message_qs))

        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        return qs.filter(thread_scope_filter_for_user(self.request.user)).distinct()

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
