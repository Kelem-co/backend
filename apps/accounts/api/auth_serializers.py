from __future__ import annotations

from accounts.models import User
from accounts.services import normalize_phone_number
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from students.models import Parent

NO_ACTIVE_PARENT_ACCOUNT_MESSAGE = (
    "No active parent account was found for this phone number."
)


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


class ParentOTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value: str) -> str:
        try:
            normalized = normalize_phone_number(value)
        except ValueError as err:
            raise serializers.ValidationError(str(err)) from err

        try:
            user = User.objects.get(
                phone_number=normalized,
                role=User.Role.PARENT,
                is_active=True,
            )
        except User.DoesNotExist as err:
            raise serializers.ValidationError(
                NO_ACTIVE_PARENT_ACCOUNT_MESSAGE,
            ) from err

        try:
            parent_profile = user.parent_profile
        except Parent.DoesNotExist as err:
            raise serializers.ValidationError(
                NO_ACTIVE_PARENT_ACCOUNT_MESSAGE,
            ) from err

        if not parent_profile.is_active:
            raise serializers.ValidationError(NO_ACTIVE_PARENT_ACCOUNT_MESSAGE)

        self.context["target_user"] = user
        return normalized


class ParentOTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.RegexField(r"^\d{6}$")

    def validate_phone_number(self, value: str) -> str:
        request_serializer = ParentOTPRequestSerializer(
            data={"phone_number": value},
            context=self.context,
        )
        request_serializer.is_valid(raise_exception=True)
        return request_serializer.validated_data["phone_number"]
