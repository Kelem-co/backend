from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

from django.conf import settings
from organizations.models import Organization

logger = logging.getLogger(__name__)


def normalize_organization_name(value: str) -> str:
    return " ".join(value.split()).casefold()


def is_active_status_description(value: str) -> bool:
    normalized = normalize_organization_name(value)
    return "active" in normalized


@dataclass(frozen=True)
class VerificationOutcome:
    verification_status: str
    organization_status: str
    verification_failure_reason: str
    verification_match_source: str
    verified_name: str
    verified_license_no: str
    verified_tin_number: str

    @property
    def requires_manual_verification(self) -> bool:
        return self.verification_status != "verified"


class ETradeClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int | None = None,
        referer: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ETRADE_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.ETRADE_API_TIMEOUT
        self.referer = referer or settings.ETRADE_API_REFERER
        self.user_agent = user_agent or settings.ETRADE_API_USER_AGENT

    def get_registration_info_by_tin(self, tin: str) -> dict[str, Any] | None:
        path = f"/Registration/GetRegistrationInfoByTin/{quote(tin)}/en"
        return self._get_json(path)

    def get_business_by_license_no(
        self,
        tin: str,
        license_no: str,
    ) -> dict[str, Any] | None:
        query = urlencode(
            {
                "LicenseNo": license_no,
                "Tin": tin,
                "Lang": "en",
            },
        )
        path = f"/BusinessMain/GetBusinessByLicenseNo?{query}"
        return self._get_json(path)

    def _get_json(self, path: str) -> dict[str, Any] | None:
        request = Request(  # noqa: S310
            url=f"{self.base_url}{path}",
            headers={
                "Accept": "application/json",
                "Referer": self.referer,
                "User-Agent": self.user_agent,
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("eTrade lookup failed: %s", exc)
            return None

        if isinstance(payload, dict):
            return payload

        logger.warning("eTrade lookup returned non-object payload: %r", payload)
        return None


def _build_verified_outcome(
    *,
    match_source: str,
    verified_name: str,
    verified_license_no: str,
    verified_tin_number: str,
) -> VerificationOutcome:
    return VerificationOutcome(
        verification_status=Organization.VerificationStatus.VERIFIED,
        organization_status=Organization.Status.ACTIVE,
        verification_failure_reason="",
        verification_match_source=match_source,
        verified_name=verified_name,
        verified_license_no=verified_license_no,
        verified_tin_number=verified_tin_number,
    )


def _build_pending_outcome(
    *,
    verification_status: str,
    failure_reason: str,
) -> VerificationOutcome:
    return VerificationOutcome(
        verification_status=verification_status,
        organization_status=Organization.Status.PENDING,
        verification_failure_reason=failure_reason,
        verification_match_source="",
        verified_name="",
        verified_license_no="",
        verified_tin_number="",
    )


def _extract_tin_match(  # noqa: C901
    *,
    registration: dict[str, Any],
    normalized_name: str,
    license_no: str,
) -> tuple[str, str, str]:
    matched_name = ""
    matched_source = ""
    matched_license = ""

    for field_name, source_name in (
        ("BusinessName", "tin_business_name"),
        ("BusinessNameAmh", "tin_business_name"),
    ):
        candidate = registration.get(field_name)
        if not isinstance(candidate, str):
            continue
        if normalize_organization_name(candidate) == normalized_name:
            matched_name = candidate
            matched_source = source_name
            break

    businesses = registration.get("Businesses")
    if not isinstance(businesses, list):
        return matched_name, matched_source, matched_license

    for business in businesses:
        if not isinstance(business, dict):
            continue

        business_license = business.get("LicenceNumber")
        if (
            license_no
            and isinstance(business_license, str)
            and business_license == license_no
        ):
            matched_license = business_license
            if not matched_name:
                trade_name = business.get("TradesName")
                if isinstance(trade_name, str):
                    matched_name = trade_name
            matched_source = "tin_license_number"

        trade_name = business.get("TradesName")
        if (
            not matched_name
            and isinstance(trade_name, str)
            and normalize_organization_name(trade_name) == normalized_name
        ):
            matched_name = trade_name
            matched_source = "tin_trade_name"

    return matched_name, matched_source, matched_license


def _has_matching_active_license(
    *,
    license_lookup: dict[str, Any] | None,
    license_no: str,
    normalized_name: str,
) -> bool:
    if license_lookup is None:
        return False

    lookup_license = license_lookup.get("LicenceNumber")
    lookup_trade_name = license_lookup.get("TradeName")
    status_description = license_lookup.get("StatusDescription")
    return (
        isinstance(lookup_license, str)
        and lookup_license == license_no
        and isinstance(lookup_trade_name, str)
        and normalize_organization_name(lookup_trade_name) == normalized_name
        and isinstance(status_description, str)
        and is_active_status_description(status_description)
    )


def verify_organization_registration(
    *,
    name: str,
    tin_number: str,
    license_no: str,
    client: ETradeClient | None = None,
) -> VerificationOutcome:
    etrade_client = client or ETradeClient()
    registration = etrade_client.get_registration_info_by_tin(tin_number)

    if registration is None:
        return _build_pending_outcome(
            verification_status=Organization.VerificationStatus.VERIFICATION_UNAVAILABLE,
            failure_reason="etrade_service_unavailable",
        )

    normalized_name = normalize_organization_name(name)
    matched_name, matched_source, matched_license = _extract_tin_match(
        registration=registration,
        normalized_name=normalized_name,
        license_no=license_no,
    )

    if license_no:
        license_lookup = etrade_client.get_business_by_license_no(
            tin=tin_number,
            license_no=license_no,
        )
        if _has_matching_active_license(
            license_lookup=license_lookup,
            license_no=license_no,
            normalized_name=normalized_name,
        ):
            lookup_trade_name = license_lookup["TradeName"]
            lookup_license = license_lookup["LicenceNumber"]
            return _build_verified_outcome(
                match_source="license_lookup",
                verified_name=lookup_trade_name,
                verified_license_no=lookup_license,
                verified_tin_number=tin_number,
            )

    if matched_source and (matched_license or matched_name):
        return _build_verified_outcome(
            match_source=matched_source,
            verified_name=matched_name,
            verified_license_no=matched_license or license_no,
            verified_tin_number=tin_number,
        )

    return _build_pending_outcome(
        verification_status=Organization.VerificationStatus.PENDING_MANUAL_REVIEW,
        failure_reason="organization_details_did_not_match_etrade_records",
    )
