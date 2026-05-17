from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "room", "sender", "content", "is_read", "created_at"]
        read_only_fields = ["id", "sender", "is_read", "created_at"]


class BroadcastSerializer(serializers.Serializer):
    parent_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of UUIDs for the target parents.",
    )
    content = serializers.CharField(
        min_length=1,
        help_text="The message content to broadcast.",
    )
