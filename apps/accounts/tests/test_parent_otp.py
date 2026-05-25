from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus
from unittest.mock import patch

import pytest
from accounts.models import ParentLoginOTP
from accounts.models import User
from accounts.services import create_parent_login_otp
from accounts.tests.factories import UserFactory
from django.utils import timezone
from rest_framework.test import APIClient
from students.models import Parent


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def active_parent_user() -> User:
    user = UserFactory(
        role=User.Role.PARENT,
        is_active=True,
        phone_number="+251911111301",
    )
    Parent.objects.create(user=user, is_active=True)
    return user


@pytest.mark.django_db
@patch("accounts.jwt_views.send_parent_otp_sms")
def test_parent_otp_request_sends_sms(
    mock_send_sms,
    api_client: APIClient,
    active_parent_user: User,
):
    response = api_client.post(
        "/auth/otp/request/",
        {"phone_number": active_parent_user.phone_number},
        format="json",
    )

    assert response.status_code == HTTPStatus.OK
    assert response.data["message"] == "OTP sent successfully."
    assert ParentLoginOTP.objects.filter(user=active_parent_user).count() == 1
    assert mock_send_sms.called


@pytest.mark.django_db
def test_parent_otp_verify_returns_tokens(
    api_client: APIClient,
    active_parent_user: User,
):
    otp_code = create_parent_login_otp(user=active_parent_user)

    response = api_client.post(
        "/auth/otp/verify/",
        {
            "phone_number": active_parent_user.phone_number,
            "otp_code": otp_code,
        },
        format="json",
    )

    assert response.status_code == HTTPStatus.OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_parent_otp_verify_rejects_wrong_code(
    api_client: APIClient,
    active_parent_user: User,
):
    create_parent_login_otp(user=active_parent_user)

    response = api_client.post(
        "/auth/otp/verify/",
        {
            "phone_number": active_parent_user.phone_number,
            "otp_code": "000000",
        },
        format="json",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.data["errors"][0]["field"] == "otp_code"


@pytest.mark.django_db
def test_parent_otp_verify_rejects_expired_code(
    api_client: APIClient,
    active_parent_user: User,
):
    create_parent_login_otp(user=active_parent_user)
    otp = active_parent_user.parent_login_otps.first()
    assert otp is not None
    otp.expires_at = timezone.now() - timedelta(minutes=1)
    otp.save(update_fields=["expires_at", "updated_at"])

    response = api_client.post(
        "/auth/otp/verify/",
        {
            "phone_number": active_parent_user.phone_number,
            "otp_code": "123456",
        },
        format="json",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.data["errors"][0]["field"] == "otp_code"


@pytest.mark.django_db
def test_parent_otp_verify_rejects_reused_code(
    api_client: APIClient,
    active_parent_user: User,
):
    otp_code = create_parent_login_otp(user=active_parent_user)

    first_response = api_client.post(
        "/auth/otp/verify/",
        {
            "phone_number": active_parent_user.phone_number,
            "otp_code": otp_code,
        },
        format="json",
    )
    second_response = api_client.post(
        "/auth/otp/verify/",
        {
            "phone_number": active_parent_user.phone_number,
            "otp_code": otp_code,
        },
        format="json",
    )

    assert first_response.status_code == HTTPStatus.OK
    assert second_response.status_code == HTTPStatus.BAD_REQUEST
    assert second_response.data["errors"][0]["field"] == "otp_code"


@pytest.mark.django_db
def test_parent_otp_request_rejects_inactive_parent(api_client: APIClient):
    user = UserFactory(
        role=User.Role.PARENT,
        is_active=False,
        phone_number="+251911111302",
    )
    Parent.objects.create(user=user, is_active=True)

    response = api_client.post(
        "/auth/otp/request/",
        {"phone_number": user.phone_number},
        format="json",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.data["errors"][0]["field"] == "phone_number"


@pytest.mark.django_db
def test_parent_otp_request_rejects_non_parent_user(api_client: APIClient):
    user = UserFactory(
        role=User.Role.TEACHER,
        is_active=True,
        phone_number="+251911111303",
    )

    response = api_client.post(
        "/auth/otp/request/",
        {"phone_number": user.phone_number},
        format="json",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.data["errors"][0]["field"] == "phone_number"
