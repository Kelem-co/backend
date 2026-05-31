from django.db.models import Max
from django.utils import timezone
from messaging.access import can_create_thread
from messaging.access import user_can_access_thread
from messaging.models import ChatMessage
from messaging.models import ChatThread
from messaging.models import MessageRead
from rest_framework import serializers

from media.api.serializers import MediaFileReferenceField


class ChatMessageSerializer(serializers.ModelSerializer):
    attachment = MediaFileReferenceField(required=False, allow_null=True)
    sender_id = serializers.UUIDField(source="sender.id", read_only=True)
    read_by_ids = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "thread",
            "sender",
            "sender_id",
            "text",
            "attachment",
            "read_by_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sender", "created_at", "updated_at", "read_by_ids"]
        extra_kwargs = {"thread": {"read_only": True}}

    def get_read_by_ids(self, obj):
        reader_ids = obj.read_receipts.values_list("reader_id", flat=True)
        return [str(user_id) for user_id in reader_ids]

    def validate(self, attrs):
        if not attrs.get("text") and not attrs.get("attachment"):
            message = "Either text or attachment is required."
            raise serializers.ValidationError(message)
        return attrs


class ChatThreadSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()
    last_read_at = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = [
            "id",
            "parent",
            "teacher",
            "student",
            "organization",
            "branch",
            "unread_count",
            "last_read_at",
            "latest_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "branch",
            "created_at",
            "updated_at",
            "unread_count",
            "last_read_at",
            "latest_message",
        ]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        return (
            obj.messages.exclude(sender=request.user)
            .exclude(read_receipts__reader=request.user)
            .count()
        )

    def get_last_read_at(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        result = MessageRead.objects.filter(
            message__thread=obj,
            reader=request.user,
        ).aggregate(last=Max("read_at"))
        return result["last"]

    def get_latest_message(self, obj):
        latest = (
            obj.messages.select_related("sender", "attachment")
            .order_by("created_at")
            .last()
        )
        if latest is None:
            return None
        return ChatMessageSerializer(latest, context=self.context).data

    def validate(self, attrs):
        allowed = can_create_thread(
            str(attrs["parent"].id),
            str(attrs["teacher"].id),
            str(attrs["student"].id),
        )
        if not allowed:
            message = "Parent/student/teacher relationship is not eligible for chat."
            raise serializers.ValidationError(message)

        student = attrs["student"]
        attrs["organization"] = student.organization
        attrs["branch"] = student.branch
        return attrs


class MarkReadSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        thread = self.context["thread"]
        user = self.context["request"].user
        if not user_can_access_thread(user, thread):
            message = "You do not have access to this thread."
            raise serializers.ValidationError(message)

        if attrs.get("message_id"):
            exists = thread.messages.filter(id=attrs["message_id"]).exists()
            if not exists:
                message = "message_id must belong to this thread."
                raise serializers.ValidationError(message)
        return attrs

    def save(self):
        thread = self.context["thread"]
        user = self.context["request"].user
        message_id = self.validated_data.get("message_id")
        now = timezone.now()

        qs = thread.messages.exclude(sender=user).exclude(read_receipts__reader=user)
        if message_id:
            qs = qs.filter(id=message_id)

        created = []
        for msg in qs:
            obj, was_created = MessageRead.objects.get_or_create(
                message=msg,
                reader=user,
                defaults={"read_at": now},
            )
            if was_created:
                created.append(obj)
        return created


class ResolveThreadSerializer(serializers.Serializer):
    student = serializers.UUIDField(required=True)
    teacher = serializers.UUIDField(required=False)
    parent = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not attrs.get("teacher") and not attrs.get("parent"):
            message = "Either teacher or parent is required to resolve a thread."
            raise serializers.ValidationError(message)
        return attrs
