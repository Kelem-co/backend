from http import HTTPStatus

from django.urls import reverse
from organizations.models import Organization


class TestOrganizationAdmin:
    def test_changelist(self, admin_client, organization: Organization):
        url = reverse("admin:organizations_organization_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_search(self, admin_client, organization: Organization):
        url = reverse("admin:organizations_organization_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:organizations_organization_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_organization(self, admin_client, organization: Organization):
        url = reverse(
            "admin:organizations_organization_change",
            kwargs={"object_id": organization.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_approve_view(self, admin_client, organization: Organization):
        organization.status = Organization.Status.PENDING
        organization.verification_status = (
            Organization.VerificationStatus.PENDING_MANUAL_REVIEW
        )
        organization.verification_failure_reason = "manual_review_required"
        organization.save()

        url = reverse(
            "admin:organizations_organization_approve",
            kwargs={"object_id": organization.pk},
        )
        response = admin_client.get(url)

        organization.refresh_from_db()

        assert response.status_code == HTTPStatus.FOUND
        assert organization.status == Organization.Status.ACTIVE
        assert (
            organization.verification_status == Organization.VerificationStatus.VERIFIED
        )
        assert organization.verification_failure_reason == ""
        assert organization.verification_checked_at is not None

    def test_send_to_review_view(self, admin_client, organization: Organization):
        organization.status = Organization.Status.ACTIVE
        organization.verification_status = Organization.VerificationStatus.VERIFIED
        organization.verification_failure_reason = ""
        organization.save()

        url = reverse(
            "admin:organizations_organization_send_to_review",
            kwargs={"object_id": organization.pk},
        )
        response = admin_client.get(url)

        organization.refresh_from_db()

        assert response.status_code == HTTPStatus.FOUND
        assert organization.status == Organization.Status.PENDING
        assert (
            organization.verification_status
            == Organization.VerificationStatus.PENDING_MANUAL_REVIEW
        )
        assert organization.verification_failure_reason == "manual_review_required"
        assert organization.verification_checked_at is not None
