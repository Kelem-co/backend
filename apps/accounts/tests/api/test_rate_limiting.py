from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from accounts.api.views import UserViewSet
from django.core.cache import cache
from django.urls import resolve
from rest_framework.settings import api_settings
from rest_framework.settings import reload_api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

if TYPE_CHECKING:
    from accounts.models import User

ALLOWED_REQUEST_COUNT = 2


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def mock_async_email(monkeypatch: pytest.MonkeyPatch) -> Mock:
    delayed_task = Mock()
    monkeypatch.setattr("accounts.email.send_email_task.delay", delayed_task)
    return delayed_task


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def tiny_throttle_settings(settings):
    original_api_view_throttle_classes = APIView.throttle_classes
    original_user_viewset_throttle_classes = UserViewSet.throttle_classes
    signup_view_class = resolve("/auth/users/").func.cls
    original_signup_viewset_throttle_classes = signup_view_class.throttle_classes
    original_anon_rates = AnonRateThrottle.THROTTLE_RATES.copy()
    original_user_rates = UserRateThrottle.THROTTLE_RATES.copy()
    rest_framework_settings = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "anon": "2/minute",
            "user": "2/minute",
        },
    }

    settings.REST_FRAMEWORK = rest_framework_settings
    reload_api_settings(setting="REST_FRAMEWORK", value=rest_framework_settings)
    APIView.throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
    UserViewSet.throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
    signup_view_class.throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
    AnonRateThrottle.THROTTLE_RATES = {"anon": "2/minute", "user": "2/minute"}
    UserRateThrottle.THROTTLE_RATES = {"anon": "2/minute", "user": "2/minute"}

    yield

    APIView.throttle_classes = original_api_view_throttle_classes
    UserViewSet.throttle_classes = original_user_viewset_throttle_classes
    signup_view_class.throttle_classes = original_signup_viewset_throttle_classes
    AnonRateThrottle.THROTTLE_RATES = original_anon_rates
    UserRateThrottle.THROTTLE_RATES = original_user_rates
    reload_api_settings(setting="REST_FRAMEWORK", value=settings.REST_FRAMEWORK)


@pytest.mark.django_db
def test_signup_is_rate_limited(
    api_client: APIClient,
    tiny_throttle_settings,
):
    payload = {
        "email": "new-user@example.com",
        "password": "strong-password-123",
        "name": "New User",
    }

    first_response = api_client.post("/auth/users/", payload, format="json")
    second_response = api_client.post("/auth/users/", payload, format="json")
    third_response = api_client.post("/auth/users/", payload, format="json")

    assert first_response.status_code == HTTPStatus.CREATED
    assert second_response.status_code == HTTPStatus.BAD_REQUEST
    assert third_response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert third_response.data["errors"][0]["code"] == "throttled"
    assert third_response.data["errors"][0]["field"] is None


@pytest.mark.django_db
def test_authenticated_api_requests_are_rate_limited(
    api_client: APIClient,
    tiny_throttle_settings,
    user: User,
):
    api_client.force_authenticate(user=user)

    first_response = api_client.get("/api/users/me/")
    second_response = api_client.get("/api/users/me/")
    third_response = api_client.get("/api/users/me/")

    assert first_response.status_code == HTTPStatus.OK
    assert second_response.status_code == HTTPStatus.OK
    assert third_response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert third_response.data["errors"][0]["code"] == "throttled"
    assert third_response.data["errors"][0]["field"] is None
