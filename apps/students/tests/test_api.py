import pytest
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from students.api.views import ParentViewSet
from students.api.views import StudentViewSet
from students.tests.factories import ParentFactory
from students.tests.factories import ParentStudentLinkFactory
from students.tests.factories import StudentFactory


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
        return BranchFactory(school__organization=organization)

    @pytest.fixture
    def section(self, organization, branch):
        grade = GradeFactory(organization=organization, branch=branch)
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
        )

    def test_student_crud(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)

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
            "status": "ACTIVE",
        }
        response = api_client.post("/api/students/", data)
        assert response.status_code == status.HTTP_201_CREATED
        student_id = response.data["id"]

        response = api_client.get("/api/students/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        response = api_client.get(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice"

        response = api_client.patch(
            f"/api/students/{student_id}/",
            {"first_name": "Alice Updated"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice Updated"

        response = api_client.delete(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_parent_crud_and_custom_endpoints(
        self,
        api_client,
        user,
        organization,
        branch,
        section,
    ):
        api_client.force_authenticate(user=user)
        parent_user = UserFactory()

        create_payload = {
            "user": str(parent_user.id),
            "organizations": [str(organization.id)],
            "branches": [str(branch.id)],
            "secondary_phone_number": "+251911000001",
            "occupation": "Engineer",
            "work_address": "HQ Building",
            "relationship_notes": "Evening pickup",
            "emergency_contact_name": "Aster",
            "emergency_contact_phone": "+251911000002",
            "is_active": True,
        }
        response = api_client.post("/api/parents/", create_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        parent_id = response.data["id"]

        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        link_response = api_client.post(
            "/api/parent-links/",
            {
                "student": str(student.id),
                "parent": parent_id,
                "relationship_type": "MOTHER",
                "is_primary_contact": True,
            },
            format="json",
        )
        assert link_response.status_code == status.HTTP_201_CREATED

        response = api_client.get("/api/parents/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        response = api_client.get(
            f"/api/parents/?branch={branch.id}&organization={organization.id}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["occupation"] == "Engineer"

        response = api_client.get(f"/api/parents/{parent_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_details"]["email"] == parent_user.email

        response = api_client.patch(
            f"/api/parents/{parent_id}/",
            {"occupation": "Doctor"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["occupation"] == "Doctor"

        response = api_client.get(f"/api/parents/by-branch/?branch={branch.id}")
        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == parent_id for item in response.data)

        response = api_client.get(
            f"/api/parents/by-organization/?organization={organization.id}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == parent_id for item in response.data)

        response = api_client.get(f"/api/parents/{parent_id}/branches/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == str(branch.id)

        response = api_client.get(f"/api/parents/{parent_id}/organizations/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == str(organization.id)

        response = api_client.get(f"/api/parents/{parent_id}/students/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == str(student.id)

    def test_parent_link_crud(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        parent = ParentFactory(organizations=[organization], branches=[branch])

        data = {
            "student": str(student.id),
            "parent": str(parent.id),
            "relationship_type": "FATHER",
            "is_primary_contact": True,
        }
        response = api_client.post("/api/parent-links/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        link_id = response.data["id"]

        response = api_client.get("/api/parent-links/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert response.data["results"][0]["parent_details"]["id"] == str(parent.id)

        response = api_client.delete(f"/api/parent-links/{link_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_student_queryset_includes_branch_admin_branch(self, user):
        organization = OrganizationFactory()
        branch = BranchFactory(school__organization=organization)
        grade = GradeFactory(organization=organization, branch=branch)
        section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
        )
        visible_student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        foreign_student = StudentFactory()
        BranchAdminFactory(user=user, branch=branch)
        view = StudentViewSet()
        request = APIRequestFactory().get("/fake-url/")
        request.user = user
        request.query_params = request.GET
        view.request = request

        queryset = view.get_queryset()

        assert set(queryset) == {visible_student}
        assert foreign_student not in queryset

    def test_parent_queryset_includes_branch_admin_branch(self, user):
        organization = OrganizationFactory()
        branch = BranchFactory(school__organization=organization)
        visible_parent = ParentFactory(organizations=[organization], branches=[branch])
        foreign_parent = ParentFactory()
        BranchAdminFactory(user=user, branch=branch, organization=organization)
        view = ParentViewSet()
        request = APIRequestFactory().get("/fake-url/")
        request.user = user
        request.query_params = request.GET
        view.request = request

        queryset = view.get_queryset()

        assert set(queryset) == {visible_parent}
        assert foreign_parent not in queryset

    def test_parent_me_and_my_students(self, api_client, organization, branch, section):
        parent_user = UserFactory(role="PARENT")
        parent = ParentFactory(
            user=parent_user,
            organizations=[organization],
            branches=[branch],
        )
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        ParentStudentLinkFactory(student=student, parent=parent)
        api_client.force_authenticate(user=parent_user)

        response = api_client.get("/api/parents/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(parent.id)

        response = api_client.get("/api/parents/my-students/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == str(student.id)

    def test_student_schema_lists_manual_filters(self, api_client):
        api_client.force_authenticate(
            user=UserFactory(is_staff=True, is_superuser=True),
        )

        response = api_client.get("/api/schema/")

        assert response.status_code == status.HTTP_200_OK
        parameters = response.data["paths"]["/api/students/"]["get"]["parameters"]
        parameter_names = {parameter["name"] for parameter in parameters}

        assert {
            "section",
            "grade",
            "branch",
            "organization",
            "academic_year",
            "status",
            "gender",
        }.issubset(parameter_names)

    def test_parent_schema_lists_manual_filters(self, api_client):
        api_client.force_authenticate(
            user=UserFactory(is_staff=True, is_superuser=True),
        )

        response = api_client.get("/api/schema/")

        assert response.status_code == status.HTTP_200_OK
        parameters = response.data["paths"]["/api/parents/"]["get"]["parameters"]
        parameter_names = {parameter["name"] for parameter in parameters}

        assert {
            "organization",
            "branch",
            "user",
            "occupation",
            "is_active",
        }.issubset(parameter_names)
