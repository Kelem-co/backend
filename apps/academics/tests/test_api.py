import pytest
from rest_framework import status
from rest_framework.test import APIClient
from academics.tests.factories import AcademicYearFactory, GradeFactory, SectionFactory, SubjectFactory
from accounts.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory

@pytest.mark.django_db
class TestAcademicsAPI:
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

    def test_academic_year_crud(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)
        
        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "name": "2024/2025",
            "start_date": "2024-09-01",
            "end_date": "2025-06-30",
            "is_current": True
        }
        response = api_client.post("/api/academic-years/", data)
        assert response.status_code == status.HTTP_201_CREATED
        year_id = response.data["id"]

        # List
        response = api_client.get("/api/academic-years/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Retrieve
        response = api_client.get(f"/api/academic-years/{year_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "2024/2025"

        # Update
        response = api_client.patch(f"/api/academic-years/{year_id}/", {"name": "2024/25 UPDATED"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "2024/25 UPDATED"

        # Delete
        response = api_client.delete(f"/api/academic-years/{year_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_grade_crud(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)
        
        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "name": "Grade 10",
            "level": 10
        }
        response = api_client.post("/api/grades/", data)
        assert response.status_code == status.HTTP_201_CREATED
        grade_id = response.data["id"]

        # List
        response = api_client.get("/api/grades/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Update
        response = api_client.patch(f"/api/grades/{grade_id}/", {"name": "Grade 10 Updated"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Grade 10 Updated"

        # Delete
        response = api_client.delete(f"/api/grades/{grade_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_section_crud(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)
        grade = GradeFactory(organization=organization, branch=branch)
        
        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "grade": str(grade.id),
            "name": "Section A"
        }
        response = api_client.post("/api/sections/", data)
        assert response.status_code == status.HTTP_201_CREATED
        section_id = response.data["id"]

        # List
        response = api_client.get("/api/sections/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Delete
        response = api_client.delete(f"/api/sections/{section_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_subject_crud(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)
        grade = GradeFactory(organization=organization, branch=branch)
        
        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "grade": str(grade.id),
            "name": "Mathematics",
            "code": "MATH101"
        }
        response = api_client.post("/api/subjects/", data)
        assert response.status_code == status.HTTP_201_CREATED
        subject_id = response.data["id"]

        # List
        response = api_client.get("/api/subjects/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Delete
        response = api_client.delete(f"/api/subjects/{subject_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
