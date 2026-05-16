from __future__ import annotations

from organizations.models import Organization
from organizations.services.etrade import ETradeClient
from organizations.services.etrade import verify_organization_registration


class StubETradeClient(ETradeClient):
    def __init__(
        self,
        *,
        registration_response: dict | None,
        license_response: dict | None,
    ) -> None:
        self.registration_response = registration_response
        self.license_response = license_response

    def get_registration_info_by_tin(self, tin: str) -> dict | None:
        return self.registration_response

    def get_business_by_license_no(
        self,
        tin: str,
        license_no: str,
    ) -> dict | None:
        return self.license_response


class TestVerifyOrganizationRegistration:
    def test_tin_business_license_match_returns_verified(self) -> None:
        client = StubETradeClient(
            registration_response={
                "Tin": "1234567890",
                "Businesses": [
                    {
                        "LicenceNumber": "LIC-123",
                        "TradesName": "Example Trading",
                    },
                ],
            },
            license_response=None,
        )

        result = verify_organization_registration(
            name="Different Name",
            tin_number="1234567890",
            license_no="LIC-123",
            client=client,
        )

        assert result.verification_status == Organization.VerificationStatus.VERIFIED
        assert result.organization_status == Organization.Status.ACTIVE
        assert result.verification_match_source == "tin_license_number"
        assert result.verified_license_no == "LIC-123"
        assert result.verified_tin_number == "1234567890"

    def test_tin_business_name_match_returns_verified(self) -> None:
        client = StubETradeClient(
            registration_response={
                "Tin": "1234567890",
                "BusinessName": "Example Trading PLC",
            },
            license_response=None,
        )

        result = verify_organization_registration(
            name="  example trading plc  ",
            tin_number="1234567890",
            license_no="",
            client=client,
        )

        assert result.verification_status == Organization.VerificationStatus.VERIFIED
        assert result.verification_match_source == "tin_business_name"
        assert result.verified_name == "Example Trading PLC"

    def test_tin_trade_name_match_returns_verified(self) -> None:
        client = StubETradeClient(
            registration_response={
                "Tin": "1234567890",
                "Businesses": [
                    {
                        "TradesName": "Example Trading PLC",
                    },
                ],
            },
            license_response=None,
        )

        result = verify_organization_registration(
            name="example trading plc",
            tin_number="1234567890",
            license_no="",
            client=client,
        )

        assert result.verification_status == Organization.VerificationStatus.VERIFIED
        assert result.verification_match_source == "tin_trade_name"
        assert result.verified_name == "Example Trading PLC"

    def test_license_lookup_match_returns_verified(self) -> None:
        client = StubETradeClient(
            registration_response={
                "Tin": "1234567890",
                "BusinessName": "Mismatch Name",
                "Businesses": [],
            },
            license_response={
                "OwnerTIN": "1234567890",
                "TradeName": "Example Trading PLC",
                "LicenceNumber": "LIC-123",
                "StatusDescription": "Is active, needs to be renewed",
            },
        )

        result = verify_organization_registration(
            name="Example Trading PLC",
            tin_number="1234567890",
            license_no="LIC-123",
            client=client,
        )

        assert result.verification_status == Organization.VerificationStatus.VERIFIED
        assert result.verification_match_source == "license_lookup"
        assert result.verified_name == "Example Trading PLC"
        assert result.verified_license_no == "LIC-123"

    def test_empty_payload_returns_pending_manual_review(self) -> None:
        client = StubETradeClient(
            registration_response={},
            license_response=None,
        )

        result = verify_organization_registration(
            name="Example Trading PLC",
            tin_number="1234567890",
            license_no="LIC-123",
            client=client,
        )

        assert (
            result.verification_status
            == Organization.VerificationStatus.PENDING_MANUAL_REVIEW
        )
        assert result.organization_status == Organization.Status.PENDING
        assert result.requires_manual_verification is True
        assert (
            result.verification_failure_reason
            == "organization_details_did_not_match_etrade_records"
        )

    def test_unavailable_service_returns_verification_unavailable(self) -> None:
        client = StubETradeClient(
            registration_response=None,
            license_response=None,
        )

        result = verify_organization_registration(
            name="Example Trading PLC",
            tin_number="1234567890",
            license_no="LIC-123",
            client=client,
        )

        assert (
            result.verification_status
            == Organization.VerificationStatus.VERIFICATION_UNAVAILABLE
        )
        assert result.organization_status == Organization.Status.PENDING
        assert result.requires_manual_verification is True
        assert result.verification_failure_reason == "etrade_service_unavailable"
