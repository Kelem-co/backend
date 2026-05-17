from __future__ import annotations

import pytest
from accounts.tests.factories import UserFactory
from organizations.api.views import OrganizationViewSet
from organizations.services.etrade import VerificationOutcome
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

from media.models import StatusChoices
from media.tests.factories import MediaFileFactory


@pytest.mark.django_db
class TestOrganizationViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_organization = OrganizationFactory(owner=user)
        foreign_organization = OrganizationFactory()
        view = OrganizationViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_organization]
        assert foreign_organization not in queryset

    def test_create_returns_verified_response(
        self,
        api_client: APIClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user = UserFactory()
        api_client.force_authenticate(user=user)

        monkeypatch.setattr(
            "organizations.services.organization_creation.verify_organization_registration",
            lambda **_: VerificationOutcome(
                verification_status="verified",
                organization_status="ACTIVE",
                verification_failure_reason="",
                verification_match_source="license_lookup",
                verified_name="Example Trading PLC",
                verified_license_no="LIC-123",
                verified_tin_number="1234567890",
            ),
        )

        response = api_client.post(
            "/api/organizations/",
            {
                "name": "Example Trading PLC",
                "trade_name": "Example Trading",
                "tin_number": "1234567890",
                "license_no": "LIC-123",
                "client_full_name": "Owner Name",
                "business_address": "Addis Ababa",
                "business_phone_number": "0911000000",
                "client_phone_number": "0911000001",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tin_number"] == "1234567890"
        assert response.data["status"] == "ACTIVE"
        assert response.data["verification_status"] == "verified"
        assert response.data["verification_failure_reason"] == ""
        assert response.data["requires_manual_verification"] is False

    def test_create_accepts_business_license_media_reference(
        self,
        api_client: APIClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user = UserFactory()
        api_client.force_authenticate(user=user)
        media = MediaFileFactory(
            uploaded_by=user,
            status=StatusChoices.UPLOADED,
            content_type="image/png",
        )

        monkeypatch.setattr(
            "organizations.services.organization_creation.verify_organization_registration",
            lambda **_: VerificationOutcome(
                verification_status="verified",
                organization_status="ACTIVE",
                verification_failure_reason="",
                verification_match_source="license_lookup",
                verified_name="Example Trading PLC",
                verified_license_no="LIC-123",
                verified_tin_number="1234567890",
            ),
        )

        response = api_client.post(
            "/api/organizations/",
            {
                "name": "Example Trading PLC",
                "trade_name": "Example Trading",
                "tin_number": "1234567890",
                "license_no": "LIC-123",
                "client_full_name": "Owner Name",
                "business_address": "Addis Ababa",
                "business_phone_number": "0911000000",
                "client_phone_number": "0911000001",
                "business_license_image": str(media.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["business_license_image"]) == str(media.id)

    def test_create_returns_pending_manual_review_when_inconclusive(
        self,
        api_client: APIClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user = UserFactory()
        api_client.force_authenticate(user=user)

        monkeypatch.setattr(
            "organizations.services.organization_creation.verify_organization_registration",
            lambda **_: VerificationOutcome(
                verification_status="pending_manual_review",
                organization_status="PENDING",
                verification_failure_reason="organization_details_did_not_match_etrade_records",
                verification_match_source="",
                verified_name="",
                verified_license_no="",
                verified_tin_number="",
            ),
        )

        response = api_client.post(
            "/api/organizations/",
            {
                "name": "Example Trading PLC",
                "trade_name": "Example Trading",
                "tin_number": "1234567890",
                "license_no": "LIC-123",
                "client_full_name": "Owner Name",
                "business_address": "Addis Ababa",
                "business_phone_number": "0911000000",
                "client_phone_number": "0911000001",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "PENDING"
        assert response.data["verification_status"] == "pending_manual_review"
        assert (
            response.data["verification_failure_reason"]
            == "organization_details_did_not_match_etrade_records"
        )
        assert response.data["requires_manual_verification"] is True

    def test_create_returns_verification_unavailable_when_service_fails(
        self,
        api_client: APIClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user = UserFactory()
        api_client.force_authenticate(user=user)

        monkeypatch.setattr(
            "organizations.services.organization_creation.verify_organization_registration",
            lambda **_: VerificationOutcome(
                verification_status="verification_unavailable",
                organization_status="PENDING",
                verification_failure_reason="etrade_service_unavailable",
                verification_match_source="",
                verified_name="",
                verified_license_no="",
                verified_tin_number="",
            ),
        )

        response = api_client.post(
            "/api/organizations/",
            {
                "name": "Example Trading PLC",
                "trade_name": "Example Trading",
                "tin_number": "1234567890",
                "license_no": "LIC-123",
                "client_full_name": "Owner Name",
                "business_address": "Addis Ababa",
                "business_phone_number": "0911000000",
                "client_phone_number": "0911000001",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "PENDING"
        assert response.data["verification_status"] == "verification_unavailable"
        assert (
            response.data["verification_failure_reason"] == "etrade_service_unavailable"
        )
        assert response.data["requires_manual_verification"] is True
