import pytest
from rest_framework import status
from rest_framework.test import APIClient
from students.tests.factories import StudentFactory, ParentStudentLinkFactory
from academics.tests.factories import SectionFactory
from accounts.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory

@pytest.mark.django_db
class TestStudentsAPI:
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

    @pytest.fixture
    def section(self, organization, branch):
        return SectionFactory(organization=organization, branch=branch)

    def test_student_crud(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)
        
        # Create
        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": "FEMALE",
            "date_of_birth": "2015-05-20",
            "roll_no": "R101",
            "current_section": str(section.id),
            "admission_date": "2023-09-01",
            "status": "ACTIVE"
        }
        response = api_client.post("/api/students/", data)
        assert response.status_code == status.HTTP_201_CREATED
        student_id = response.data["id"]

        # List
        response = api_client.get("/api/students/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Retrieve
        response = api_client.get(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice"

        # Update
        response = api_client.patch(f"/api/students/{student_id}/", {"first_name": "Alice Updated"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice Updated"

        # Delete
        response = api_client.delete(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_parent_link_crud(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)
        student = StudentFactory(organization=organization, branch=branch, current_section=section)
        parent = UserFactory()
        
        # Create
        data = {
            "student": str(student.id),
            "parent": str(parent.id),
            "relationship_type": "FATHER",
            "is_primary_contact": True
        }
        response = api_client.post("/api/parent-links/", data)
        assert response.status_code == status.HTTP_201_CREATED
        link_id = response.data["id"]

        # List
        response = api_client.get("/api/parent-links/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Delete
        response = api_client.delete(f"/api/parent-links/{link_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
