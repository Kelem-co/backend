from datetime import date

import pytest
from academics.models import AcademicYear
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from teachers.models import Teacher
from teachers.models import TeacherSubjectAssignment

from assessments.models import Assessment


@pytest.mark.django_db
class TestAssessmentsAPI:
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
    def academic_year(self, organization, branch):
        return AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            name="2025/2026",
        )

    @pytest.fixture
    def grade(self, organization, branch):
        return GradeFactory(
            organization=organization,
            branch=branch,
            name="Grade 7",
            level=7,
        )

    @pytest.fixture
    def section(self, organization, branch, grade, academic_year):
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
            name="A",
        )

    @pytest.fixture
    def subject(self, organization, branch, grade):
        return SubjectFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            name="Mathematics",
            code="MATH-7",
        )

    @pytest.fixture
    def teacher(self, organization, branch):
        return Teacher.objects.create(
            user=UserFactory(role="TEACHER", name="Abel"),
            organization=organization,
            branch=branch,
            employee_id="EMP-1001",
            specialization="Mathematics",
        )

    def test_list_can_filter_by_teacher_section_and_subject(  # noqa: PLR0913
        self,
        api_client,
        owner,
        organization,
        branch,
        academic_year,
        section,
        subject,
        teacher,
    ):
        api_client.force_authenticate(user=owner)

        matching_assignment = TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )
        matching_assessment = Assessment.objects.create(
            organization=organization,
            branch=branch,
            teacher_assignment=matching_assignment,
            title="Algebra Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=20,
            passing_marks=10,
            due_date=date(2026, 1, 15),
            status=Assessment.Status.PUBLISHED,
        )

        other_teacher = Teacher.objects.create(
            user=UserFactory(role="TEACHER", name="Beth"),
            organization=organization,
            branch=branch,
            employee_id="EMP-1002",
            specialization="Physics",
        )
        other_assignment = TeacherSubjectAssignment.objects.create(
            teacher=other_teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )
        Assessment.objects.create(
            organization=organization,
            branch=branch,
            teacher_assignment=other_assignment,
            title="Geometry Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=20,
            passing_marks=10,
            due_date=date(2026, 1, 16),
            status=Assessment.Status.PUBLISHED,
        )

        response = api_client.get(
            "/api/assessments/",
            {
                "teacher": str(teacher.id),
                "section": str(section.id),
                "subject": str(subject.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(matching_assessment.id)
        assert str(response.data["results"][0]["teacher_assignment"]) == str(
            matching_assignment.id,
        )
        assert response.data["results"][0]["teacher_name"] == "Abel"
        assert response.data["results"][0]["section_name"] == section.name
        assert response.data["results"][0]["subject_name"] == subject.name
