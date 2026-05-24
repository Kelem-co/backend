from __future__ import annotations

from typing import Any

from accounts.models import User
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization
from rest_framework_simplejwt.authentication import default_user_authentication_rule

ORGANIZATION_LOGIN_BLOCK_MESSAGE = _(
    "Your organization account is pending verification approval.",
)


def is_organization_login_allowed(user: Any) -> bool:
    if not user or getattr(user, "role", "") != User.Role.ORGANIZATION:
        return True

    return user.organizations.filter(
        status=Organization.Status.ACTIVE,
        verification_status=Organization.VerificationStatus.VERIFIED,
    ).exists()


def user_authentication_rule(user: Any) -> bool:
    return default_user_authentication_rule(user) and is_organization_login_allowed(
        user,
    )
