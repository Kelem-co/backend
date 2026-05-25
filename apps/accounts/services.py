from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from accounts.models import ApprovalLoginToken
from accounts.models import User
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

from .auth import OrganizationLoginState
from .auth import get_organization_login_state

APPROVAL_MAGIC_LINK_EXPIRY = timedelta(hours=24)
APPROVAL_MAGIC_LINK_PATH = "organization-approval/{uid}/{token}"


@dataclass(frozen=True)
class ApprovalMagicLink:
    path: str
    raw_token: str


def _hash_token_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def build_frontend_approval_magic_link(*, user: User, raw_token: str) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return APPROVAL_MAGIC_LINK_PATH.format(uid=uid, token=raw_token)


def create_approval_magic_link(*, user: User) -> ApprovalMagicLink:
    secret = secrets.token_urlsafe(32)
    token_record = ApprovalLoginToken.objects.create(
        user=user,
        token_hash=_hash_token_secret(secret),
        expires_at=timezone.now() + APPROVAL_MAGIC_LINK_EXPIRY,
    )
    raw_token = f"{token_record.pk}.{secret}"
    return ApprovalMagicLink(
        path=build_frontend_approval_magic_link(user=user, raw_token=raw_token),
        raw_token=raw_token,
    )


def _parse_raw_token(raw_token: str) -> tuple[str, str]:
    token_id, separator, secret = raw_token.partition(".")
    if not separator or not token_id or not secret:
        raise serializers.ValidationError(
            {"token": "Invalid or expired approval link."},
        )
    return token_id, secret


@transaction.atomic
def consume_approval_magic_link(*, user: User, raw_token: str) -> ApprovalLoginToken:
    token_id, secret = _parse_raw_token(raw_token)

    try:
        token_record = ApprovalLoginToken.objects.select_for_update().get(
            pk=token_id,
            user=user,
        )
    except ApprovalLoginToken.DoesNotExist as err:
        raise serializers.ValidationError(
            {"token": "Invalid or expired approval link."},
        ) from err

    if token_record.used_at is not None or token_record.expires_at <= timezone.now():
        raise serializers.ValidationError(
            {"token": "Invalid or expired approval link."},
        )

    expected_hash = _hash_token_secret(secret)
    if not constant_time_compare(token_record.token_hash, expected_hash):
        raise serializers.ValidationError(
            {"token": "Invalid or expired approval link."},
        )

    if get_organization_login_state(user) != OrganizationLoginState.ALLOWED:
        raise serializers.ValidationError(
            {"token": "Invalid or expired approval link."},
        )

    token_record.used_at = timezone.now()
    token_record.save(update_fields=["used_at", "updated_at"])
    return token_record


def get_magic_link_email_context(
    *,
    user: User,
    raw_token: str,
    organization_name: str,
) -> dict[str, object]:
    return {
        "user": user,
        "organization_name": organization_name,
        "url": build_frontend_approval_magic_link(user=user, raw_token=raw_token),
        "domain": settings.FRONTEND_DOMAIN,
        "protocol": settings.FRONTEND_PROTOCOL,
    }
