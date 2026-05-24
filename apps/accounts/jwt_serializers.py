from __future__ import annotations

from typing import Any

from accounts.auth import ORGANIZATION_LOGIN_BLOCK_MESSAGE
from accounts.auth import is_organization_login_allowed
from django.contrib.auth import authenticate
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import default_user_authentication_rule
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class OrganizationAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        **TokenObtainPairSerializer.default_error_messages,
        "organization_not_verified": ORGANIZATION_LOGIN_BLOCK_MESSAGE,
    }

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        request = self.context.get("request")
        if request is not None:
            authenticate_kwargs["request"] = request

        self.user = authenticate(**authenticate_kwargs)

        if self.user is None or not default_user_authentication_rule(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        if not is_organization_login_allowed(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["organization_not_verified"],
                "organization_not_verified",
            )

        return super().validate(attrs)
