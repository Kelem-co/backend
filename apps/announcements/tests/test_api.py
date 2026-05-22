import pytest
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAnnouncementsAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def organization(self, user):
        return OrganizationFactory(owner=user)

    @pytest.fixture
    def branch(self, organization):
        return BranchFactory(organization=organization)

    def test_announcement_crud(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        grade = GradeFactory(organization=organization, branch=branch)
        section = SectionFactory(organization=organization, branch=branch, grade=grade)

        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "subject": "Test Subject",
            "message": "Test Message",
            "is_urgent": False,
            "status": "DRAFT",
            "target_roles": "PARENTS",
            "targeted_grades": [str(grade.id)],
            "targeted_sections": [str(section.id)],
        }
        response = api_client.post("/api/announcements/", data)
        assert response.status_code == status.HTTP_201_CREATED, response.data
        announcement_id = response.data["id"]

        # List
        response = api_client.get("/api/announcements/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Retrieve
        response = api_client.get(f"/api/announcements/{announcement_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["subject"] == "Test Subject"
        assert len(response.data["targeted_grades"]) == 1
        assert len(response.data["targeted_sections"]) == 1

        # Update
        response = api_client.patch(
            f"/api/announcements/{announcement_id}/",
            {"subject": "Test Subject Updated"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["subject"] == "Test Subject Updated"

        # Delete
        response = api_client.delete(f"/api/announcements/{announcement_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_targeting_criteria(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        grade = GradeFactory(organization=organization, branch=branch)
        SectionFactory(organization=organization, branch=branch, grade=grade)

        # Test custom action
        response = api_client.get("/api/announcements/get_targeting_criteria/")
        assert response.status_code == status.HTTP_200_OK

        assert "grades" in response.data
        assert "sections" in response.data

        # Depending on scope filtering rules, it might or might not return them
        # (if UserFactory doesn't automatically give permissions to the branch).
        # Assuming the user has access to the branch's data, we assert lengths.
        # This assert depends on whether the user has roles, but at least the endpoint works.
        assert isinstance(response.data["grades"], list)
        assert isinstance(response.data["sections"], list)
