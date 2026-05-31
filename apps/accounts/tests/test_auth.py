from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from accounts.adapters import AccountAdapter
from accounts.auth import OrganizationLoginState
from accounts.auth import get_organization_login_state
from accounts.auth import user_authentication_rule
from accounts.models import ApprovalLoginToken
from accounts.models import User
from accounts.services import create_approval_magic_link
from accounts.tests.factories import UserFactory
from allauth.account.models import EmailAddress
from allauth.account.utils import user_email
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.utils import timezone
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

    def test_web_login_allows_zero_org_organization_owner(
        self,
        rf: RequestFactory,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)
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

    def test_web_login_blocks_pending_organization_owner(
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

    def test_organization_login_state_is_allowed_for_zero_orgs(
        self,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)

        assert get_organization_login_state(user) == OrganizationLoginState.ALLOWED
        assert user_authentication_rule(user) is True

    def test_organization_login_state_is_pending_verification_without_verified_orgs(
        self,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(
            owner=user,
            status=Organization.Status.PENDING,
            verification_status=Organization.VerificationStatus.PENDING_MANUAL_REVIEW,
        )

        assert get_organization_login_state(user) == (
            OrganizationLoginState.PENDING_VERIFICATION
        )

    def test_organization_login_state_is_allowed_for_any_verified_organization(
        self,
    ) -> None:
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

        assert get_organization_login_state(user) == OrganizationLoginState.ALLOWED
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

    def test_jwt_login_allows_zero_org_organization_owner(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.ORGANIZATION, password=password)

        response = api_client.post(
            "/auth/jwt/create/",
            {"email": user.email, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_jwt_login_blocks_pending_organization_owner(
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

    def test_jwt_login_is_unchanged_for_non_organization_roles(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(role=User.Role.TEACHER, password=password)

        response = api_client.post(
            "/auth/jwt/create/",
            {"email": user.email, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        assert "access" in response.data
        assert "refresh" in response.data


@pytest.mark.django_db
class TestParentJwtPhoneLogin:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_parent_can_log_in_with_phone_number_and_password(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(
            role=User.Role.PARENT,
            password=password,
            phone_number="+251911111410",
            is_active=True,
        )

        response = api_client.post(
            "/auth/jwt/create/",
            {"phone_number": user.phone_number, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "refresh_token" in response.cookies

    def test_parent_login_rejects_wrong_password(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory(
            role=User.Role.PARENT,
            password="correct-password-123",  # noqa: S105
            phone_number="+251911111411",
            is_active=True,
        )

        response = api_client.post(
            "/auth/jwt/create/",
            {"phone_number": user.phone_number, "password": "wrong-password"},
            format="json",
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.data["errors"][0]["code"] == "no_active_account"

    def test_parent_login_rejects_inactive_parent_account(
        self,
        api_client: APIClient,
    ) -> None:
        password = "strong-password-123"  # noqa: S105
        user = UserFactory(
            role=User.Role.PARENT,
            password=password,
            phone_number="+251911111412",
            is_active=False,
        )

        response = api_client.post(
            "/auth/jwt/create/",
            {"phone_number": user.phone_number, "password": password},
            format="json",
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.data["errors"][0]["code"] == "no_active_account"


@pytest.mark.django_db
class TestOrganizationApprovalMagicLinkExchange:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_exchange_returns_tokens_for_verified_organization_owner(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(owner=user)
        magic_link = create_approval_magic_link(user=user)

        response = api_client.post(
            "/auth/organization-approval/exchange/",
            {
                "uid": magic_link.path.split("/")[1],
                "token": magic_link.raw_token,
            },
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        assert "access" in response.data
        assert "refresh" in response.data

        token_record = ApprovalLoginToken.objects.get(user=user)
        assert token_record.used_at is not None

    def test_exchange_rejects_reused_token(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(owner=user)
        magic_link = create_approval_magic_link(user=user)
        payload = {
            "uid": magic_link.path.split("/")[1],
            "token": magic_link.raw_token,
        }

        first_response = api_client.post(
            "/auth/organization-approval/exchange/",
            payload,
            format="json",
        )
        second_response = api_client.post(
            "/auth/organization-approval/exchange/",
            payload,
            format="json",
        )

        assert first_response.status_code == HTTPStatus.OK
        assert second_response.status_code == HTTPStatus.BAD_REQUEST
        assert second_response.data["errors"][0]["field"] == "token"

    def test_exchange_rejects_expired_token(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(owner=user)
        magic_link = create_approval_magic_link(user=user)
        token_record = ApprovalLoginToken.objects.get(user=user)
        token_record.expires_at = timezone.now()
        token_record.save(update_fields=["expires_at", "updated_at"])

        response = api_client.post(
            "/auth/organization-approval/exchange/",
            {
                "uid": magic_link.path.split("/")[1],
                "token": magic_link.raw_token,
            },
            format="json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["errors"][0]["field"] == "token"

    def test_exchange_rejects_pending_organization_owner(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory(role=User.Role.ORGANIZATION)
        OrganizationFactory(
            owner=user,
            status=Organization.Status.PENDING,
            verification_status=Organization.VerificationStatus.PENDING_MANUAL_REVIEW,
        )
        magic_link = create_approval_magic_link(user=user)

        response = api_client.post(
            "/auth/organization-approval/exchange/",
            {
                "uid": magic_link.path.split("/")[1],
                "token": magic_link.raw_token,
            },
            format="json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["errors"][0]["field"] == "token"
