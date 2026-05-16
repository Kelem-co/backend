from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from organizations.models import Organization
from organizations.services.etrade import ETradeClient
from organizations.services.etrade import verify_organization_registration

User = get_user_model()


def create_organization_with_verification(
    *,
    owner: User,
    validated_data: dict[str, Any],
    client: ETradeClient | None = None,
) -> Organization:
    tin_number = validated_data.get("tin_number", "")
    license_no = validated_data.get("license_no", "")
    name = validated_data["name"]

    verification = verify_organization_registration(
        name=name,
        tin_number=tin_number,
        license_no=license_no,
        client=client,
    )

    return Organization.objects.create(
        owner=owner,
        verification_checked_at=timezone.now(),
        verification_status=verification.verification_status,
        verification_failure_reason=verification.verification_failure_reason,
        verification_match_source=verification.verification_match_source,
        verified_name=verification.verified_name,
        verified_license_no=verification.verified_license_no,
        verified_tin_number=verification.verified_tin_number,
        status=verification.organization_status,
        **validated_data,
    )
