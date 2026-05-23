from datetime import date

import pytest
from academics.models import AcademicYear
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchFactory
from django.urls import reverse
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from teachers.models import Teacher
from teachers.models import TeacherQualification
from teachers.models import TeacherSubjectAssignment


@pytest.mark.django_db
class TestTeacherDetailActions:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def organization(self, owner):
        return OrganizationFactory(owner=owner)

    @pytest.fixture
    def branch(self, organization):
        return BranchFactory(school__organization=organization)

    @pytest.fixture
    def teacher(self, organization, branch):
        return Teacher.objects.create(
            user=UserFactory(role="TEACHER"),
            organization=organization,
            branch=branch,
            employee_id="EMP-1001",
            specialization="Mathematics",
        )

    @pytest.fixture
    def academic_year(self, organization, branch):
        return AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            name="2025/2026",
        )

    @pytest.fixture
    def section(self, organization, branch, academic_year):
        grade = GradeFactory(
            organization=organization,
            branch=branch,
            name="Grade 7",
            level=7,
        )
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
            name="A",
        )

    @pytest.fixture
    def subject(self, organization, branch, section):
        return SubjectFactory(
            organization=organization,
            branch=branch,
            grade=section.grade,
            name="Mathematics",
            code="MATH-7",
        )

    def test_teacher_sections_detail_action_uses_id_lookup_kwarg(  # noqa: PLR0913
        self,
        api_client,
        owner,
        teacher,
        organization,
        section,
        subject,
        academic_year,
    ):
        TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )
        api_client.force_authenticate(user=owner)

        response = api_client.get(f"/api/teachers/{teacher.id}/sections/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["sections"][0]["section_id"] == str(section.id)
        assert response.data["sections"][0]["academic_year_id"] == str(
            academic_year.id,
        )
        assert response.data["sections"][0]["subjects"] == [
            {
                "subject_id": str(subject.id),
                "subject_name": subject.name,
                "subject_code": subject.code,
            },
        ]

    def test_teacher_qualifications_detail_action_uses_id_lookup_kwarg(
        self,
        api_client,
        owner,
        teacher,
        organization,
    ):
        qualification = TeacherQualification.objects.create(
            teacher=teacher,
            organization=organization,
            degree_name="BSc",
            institution="Addis Ababa University",
            field_of_study="Mathematics",
            completion_date=date(2020, 6, 1),
        )
        api_client.force_authenticate(user=owner)

        response = api_client.get(f"/api/teachers/{teacher.id}/qualifications/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(qualification.id)
        assert response.data[0]["degree_name"] == "BSc"

    def test_teacher_list_can_filter_by_user_id(
        self,
        api_client,
        owner,
        organization,
        branch,
        teacher,
    ):
        other_teacher = Teacher.objects.create(
            user=UserFactory(role="TEACHER"),
            organization=organization,
            branch=branch,
            employee_id="EMP-1002",
            specialization="Physics",
        )
        api_client.force_authenticate(user=owner)

        response = api_client.get(f"/api/teachers/?user={teacher.user_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(teacher.id)
        assert str(response.data["results"][0]["user"]) == str(teacher.user_id)
        assert response.data["results"][0]["id"] != str(other_teacher.id)

    def test_teacher_can_list_own_profile_by_user_id(
        self,
        api_client,
        teacher,
    ):
        other_user = UserFactory(role="TEACHER")
        api_client.force_authenticate(user=teacher.user)

        response = api_client.get(f"/api/teachers/?user={teacher.user_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(teacher.id)
        assert str(response.data["results"][0]["user"]) == str(teacher.user_id)

        other_response = api_client.get(f"/api/teachers/?user={other_user.id}")

        assert other_response.status_code == status.HTTP_200_OK
        assert other_response.data["count"] == 0


@pytest.mark.django_db
def test_teacher_sections_endpoint_is_present_in_openapi_schema(admin_client):
    response = admin_client.get(f"{reverse('api-schema')}?format=json")

    assert response.status_code == status.HTTP_200_OK

    schema = response.json()
    operation = schema["paths"]["/api/teachers/{id}/sections/"]["get"]
    parameter_names = {parameter["name"] for parameter in operation["parameters"]}
    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]

    assert "academic_year" in parameter_names
    assert response_schema.endswith("/TeacherSectionsResponse")


@pytest.mark.django_db
def test_teacher_list_schema_documents_user_filter(admin_client):
    response = admin_client.get(f"{reverse('api-schema')}?format=json")

    assert response.status_code == status.HTTP_200_OK

    schema = response.json()
    operation = schema["paths"]["/api/teachers/"]["get"]
    parameter_names = {parameter["name"] for parameter in operation["parameters"]}

    assert "user" in parameter_names
