from __future__ import annotations

from enum import StrEnum
from typing import Any

from accounts.models import User
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization
from rest_framework_simplejwt.authentication import default_user_authentication_rule

ORGANIZATION_LOGIN_BLOCK_MESSAGE = _(
    "Your organization account is pending verification approval.",
)


class OrganizationLoginState(StrEnum):
    ALLOWED = "allowed"
    PENDING_VERIFICATION = "pending_verification"


def get_organization_login_state(user: Any) -> OrganizationLoginState:
    if not user or getattr(user, "role", "") != User.Role.ORGANIZATION:
        return OrganizationLoginState.ALLOWED

    organizations = user.organizations.all()
    if not organizations.exists():
        return OrganizationLoginState.ALLOWED

    has_verified_organization = organizations.filter(
        status=Organization.Status.ACTIVE,
        verification_status=Organization.VerificationStatus.VERIFIED,
    ).exists()
    if has_verified_organization:
        return OrganizationLoginState.ALLOWED

    return OrganizationLoginState.PENDING_VERIFICATION


def is_organization_login_allowed(user: Any) -> bool:
    return get_organization_login_state(user) == OrganizationLoginState.ALLOWED


def user_authentication_rule(user: Any) -> bool:
    return default_user_authentication_rule(user) and is_organization_login_allowed(
        user,
    )
