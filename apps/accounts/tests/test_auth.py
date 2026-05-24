from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from accounts.adapters import AccountAdapter
from accounts.auth import user_authentication_rule
from accounts.models import User
from accounts.tests.factories import UserFactory
from allauth.account.models import EmailAddress
from allauth.account.utils import user_email
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from organizations.models import Organization
from organizations.tests.factories import OrganizationFactory
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from django.test import RequestFactory


def _add_session(request) -> None:
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()


@pytest.mark.django_db
class TestOrganizationLoginRules:
    def test_web_login_allows_verified_organization_owner(
        self,
        rf: RequestFactory,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)
        OrganizationFactory(owner=user)
        EmailAddress.objects.create(
            user=user,
            email=user_email(user),
            primary=True,
            verified=True,
        )
        request = rf.post("/accounts/login/")
        _add_session(request)

        authenticated_user = AccountAdapter().authenticate(
            request,
            email=user.email,
            password=password,
        )

        assert authenticated_user == user

    def test_web_login_blocks_unverified_organization_owner(
        self,
        rf: RequestFactory,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)
        OrganizationFactory(
            owner=user,
            status=Organization.Status.PENDING,
            verification_status=Organization.VerificationStatus.PENDING_MANUAL_REVIEW,
        )
        EmailAddress.objects.create(
            user=user,
            email=user_email(user),
            primary=True,
            verified=True,
        )
        request = rf.post("/accounts/login/")
        _add_session(request)

        with pytest.raises(ValidationError) as exc_info:
            AccountAdapter().authenticate(
                request,
                email=user.email,
                password=password,
            )

        assert exc_info.value.messages == [
            "Your organization account is pending verification approval.",
        ]

    def test_user_authentication_rule_allows_any_verified_organization(self) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(
            owner=user,
            status=Organization.Status.PENDING,
            verification_status=Organization.VerificationStatus.PENDING_MANUAL_REVIEW,
        )
        OrganizationFactory(
            owner=user,
            status=Organization.Status.ACTIVE,
            verification_status=Organization.VerificationStatus.VERIFIED,
        )

        assert user_authentication_rule(user) is True

    def test_user_authentication_rule_does_not_change_non_organization_roles(
        self,
    ) -> None:
        user = UserFactory(role=User.Role.TEACHER)

        assert user_authentication_rule(user) is True


@pytest.mark.django_db
class TestOrganizationJwtLogin:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_jwt_login_allows_verified_organization_owner(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)
        OrganizationFactory(owner=user)

        response = api_client.post(
            "/auth/jwt/create/",
            {"email": user.email, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_jwt_login_blocks_unverified_organization_owner(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)
        OrganizationFactory(
            owner=user,
            status=Organization.Status.PENDING,
            verification_status=Organization.VerificationStatus.VERIFICATION_UNAVAILABLE,
        )

        response = api_client.post(
            "/auth/jwt/create/",
            {"email": user.email, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.data["errors"] == [
            {
                "code": "organization_not_verified",
                "detail": "Your organization account is pending verification approval.",
                "field": None,
            },
        ]
