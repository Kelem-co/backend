from __future__ import annotations

from typing import TYPE_CHECKING

from accounts.api.auth_serializers import ApprovalMagicLinkExchangeSerializer
from accounts.api.auth_serializers import ParentOTPRequestSerializer
from accounts.api.auth_serializers import ParentOTPVerifySerializer
from accounts.auth import ORGANIZATION_LOGIN_BLOCK_MESSAGE
from accounts.auth import OrganizationLoginState
from accounts.auth import get_organization_login_state
from accounts.services import consume_approval_magic_link
from accounts.services import consume_parent_login_otp
from accounts.services import create_parent_login_otp
from accounts.sms import send_parent_otp_sms
from django.contrib.auth import authenticate
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import default_user_authentication_rule
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

if TYPE_CHECKING:
    from rest_framework.request import Request


class OrganizationAwareTokenObtainPairView(TokenObtainPairView):
    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer_class = self.get_serializer_class()
        username_field = serializer_class.username_field
        authenticate_kwargs = {
            username_field: request.data.get(username_field, ""),
            "password": request.data.get("password", ""),
            "request": request,
        }
        user = authenticate(**authenticate_kwargs)

        if user is None or not default_user_authentication_rule(user):
            raise exceptions.AuthenticationFailed(
                serializer_class.default_error_messages["no_active_account"],
                "no_active_account",
            )

        login_state = get_organization_login_state(user)
        if login_state == OrganizationLoginState.PENDING_VERIFICATION:
            raise exceptions.AuthenticationFailed(
                ORGANIZATION_LOGIN_BLOCK_MESSAGE,
                "organization_not_verified",
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class OrganizationApprovalMagicLinkExchangeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ApprovalMagicLinkExchangeSerializer,
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                },
                "required": ["access", "refresh"],
            },
        },
    )
    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer = ApprovalMagicLinkExchangeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.context["target_user"]
        consume_approval_magic_link(
            user=user,
            raw_token=serializer.validated_data["token"],
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class ParentOTPRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=ParentOTPRequestSerializer)
    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer = ParentOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.context["target_user"]

        with transaction.atomic():
            otp_code = create_parent_login_otp(user=user)
            send_parent_otp_sms(
                phone_number=serializer.validated_data["phone_number"],
                otp_code=otp_code,
            )

        return Response(
            {"message": "OTP sent successfully."},
            status=status.HTTP_200_OK,
        )


class ParentOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ParentOTPVerifySerializer,
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                },
                "required": ["access", "refresh"],
            },
        },
    )
    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer = ParentOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.context["target_user"]
        consume_parent_login_otp(
            user=user,
            raw_code=serializer.validated_data["otp_code"],
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
