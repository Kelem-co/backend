from __future__ import annotations

import pytest
from accounts.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from schools.api.views import SchoolViewSet
from schools.tests.factories import SchoolFactory

from media.models import StatusChoices
from media.tests.factories import MediaFileFactory


@pytest.mark.django_db
class TestSchoolViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_school = SchoolFactory(organization__owner=user)
        foreign_school = SchoolFactory()
        view = SchoolViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_school]
        assert foreign_school not in queryset

    def test_create_accepts_logo_media_reference(
        self,
        api_client: APIClient,
    ) -> None:
        user = UserFactory()
        organization = OrganizationFactory(owner=user)
        media = MediaFileFactory(
            uploaded_by=user,
            status=StatusChoices.UPLOADED,
            content_type="image/png",
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/schools/",
            {
                "organization": str(organization.id),
                "name": "Example School",
                "description": "A school",
                "country": "Ethiopia",
                "contact_email": "school@example.com",
                "contact_phone": "0911000000",
                "logo": str(media.id),
                "website": "https://school.example.com",
                "status": "ACTIVE",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["logo"]) == str(media.id)
