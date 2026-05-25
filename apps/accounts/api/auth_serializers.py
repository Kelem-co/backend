from __future__ import annotations

from accounts.models import User
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers


class ApprovalMagicLinkExchangeSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate_uid(self, value: str) -> str:
        try:
            user_id = force_str(urlsafe_base64_decode(value))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as err:
            message = "Invalid user ID."
            raise serializers.ValidationError(message) from err

        self.context["target_user"] = user
        return value

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        user = self.context.get("target_user")
        if user is None:
            raise serializers.ValidationError({"uid": "Invalid user ID."})

        if user.role != User.Role.ORGANIZATION:
            raise serializers.ValidationError(
                {"uid": "Invalid or expired approval link."},
            )

        return attrs
