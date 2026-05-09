from http import HTTPStatus

import pytest
from rest_framework.test import APIClient

from core.users.models import User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_user_signup_accepts_extended_profile_fields(api_client: APIClient):
    payload = {
        "username": "new-user",
        "email": "new-user@example.com",
        "password": "strong-password-123",
        "father_name": "John Doe",
        "grandfather_name": "James Doe",
        "phone_number": "+15555550123",
        "address": "123 Main Street",
    }

    response = api_client.post("/auth/users/", payload, format="json")

    assert response.status_code == HTTPStatus.CREATED

    user = User.objects.get(username=payload["username"])
    assert user.email == payload["email"]
    assert user.father_name == payload["father_name"]
    assert user.grandfather_name == payload["grandfather_name"]
    assert user.phone_number == payload["phone_number"]
    assert user.address == payload["address"]
    assert user.check_password(payload["password"])


@pytest.mark.django_db
def test_user_signup_allows_address_to_be_omitted(api_client: APIClient):
    payload = {
        "username": "new-user-no-address",
        "email": "new-user-no-address@example.com",
        "password": "strong-password-123",
        "father_name": "John Doe",
        "grandfather_name": "James Doe",
        "phone_number": "+15555550124",
    }

    response = api_client.post("/auth/users/", payload, format="json")

    assert response.status_code == HTTPStatus.CREATED

    user = User.objects.get(username=payload["username"])
    assert user.address == ""
