from http import HTTPStatus
from typing import TYPE_CHECKING

from django.urls import reverse

if TYPE_CHECKING:
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
