from __future__ import annotations

from typing import TYPE_CHECKING

from accounts.api.auth_serializers import ApprovalMagicLinkExchangeSerializer
from accounts.api.auth_serializers import ParentPhoneOrEmailTokenObtainPairSerializer
from accounts.api.auth_serializers import ParentOTPRequestSerializer
from accounts.api.auth_serializers import ParentOTPVerifySerializer
from accounts.auth import ORGANIZATION_LOGIN_BLOCK_MESSAGE
from accounts.auth import OrganizationLoginState
from accounts.auth import get_organization_login_state
from accounts.services import consume_approval_magic_link
from accounts.services import consume_parent_login_otp
from accounts.services import create_parent_login_otp
from accounts.sms import send_parent_otp_sms
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import default_user_authentication_rule
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView

if TYPE_CHECKING:
    from rest_framework.request import Request


def _set_refresh_cookie(response: Response, refresh: RefreshToken | str) -> None:
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=str(refresh),
        httponly=settings.JWT_REFRESH_COOKIE_HTTPONLY,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        domain=settings.JWT_REFRESH_COOKIE_DOMAIN,
    )


def _delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        domain=settings.JWT_REFRESH_COOKIE_DOMAIN,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


class OrganizationAwareTokenObtainPairView(TokenObtainPairView):
    serializer_class = ParentPhoneOrEmailTokenObtainPairSerializer

    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        if user is None or not default_user_authentication_rule(user):
            raise exceptions.AuthenticationFailed(
                serializer.error_messages["no_active_account"],
                "no_active_account",
            )

        login_state = get_organization_login_state(user)
        if login_state == OrganizationLoginState.PENDING_VERIFICATION:
            raise exceptions.AuthenticationFailed(
                ORGANIZATION_LOGIN_BLOCK_MESSAGE,
                "organization_not_verified",
            )

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        refresh_token = serializer.validated_data.get("refresh")
        if refresh_token:
            _set_refresh_cookie(response, refresh_token)
        return response


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

    @extend_schema(request=ParentOTPVerifySerializer)
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
        response = Response(
            {
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, refresh)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        cookie_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        body_refresh = (
            request.data.get("refresh") if isinstance(request.data, dict) else None
        )
        refresh_token = cookie_refresh or body_refresh
        if not refresh_token:
            msg = "Refresh token missing from cookie and request body."
            raise InvalidToken(msg)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        # Rotate cookie when refresh rotation is enabled.
        rotated_refresh = serializer.validated_data.get("refresh")
        if rotated_refresh:
            _set_refresh_cookie(response, rotated_refresh)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        response = Response(
            {"message": "Logged out successfully.", "timestamp": timezone.now()},
            status=status.HTTP_200_OK,
        )
        _delete_refresh_cookie(response)
        return response
