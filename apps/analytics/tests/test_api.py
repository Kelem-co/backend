import pytest
from academics.models import AcademicYear
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from accounts.tests.factories import UserFactory
from analytics.models import InterventionLog
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from students.tests.factories import StudentFactory
from teachers.models import Teacher
from teachers.models import TeacherSubjectAssignment


@pytest.mark.django_db
class TestInterventionLogTeacherAccessAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def organization(self):
        return OrganizationFactory()

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
        return GradeFactory(organization=organization, branch=branch, level=9)

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
    def other_section(self, organization, branch, grade, academic_year):
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
            name="B",
        )

    @pytest.fixture
    def subject(self, organization, branch, grade):
        return SubjectFactory(organization=organization, branch=branch, grade=grade)

    @pytest.fixture
    def teacher(self, organization, branch):
        return Teacher.objects.create(
            user=UserFactory(role="TEACHER", name="Assigned Teacher"),
            organization=organization,
            branch=branch,
            employee_id="EMP-IL-1",
            specialization="English",
        )

    @pytest.fixture
    def student(self, organization, branch, section):
        return StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )

    @pytest.fixture
    def other_student(self, organization, branch, other_section):
        return StudentFactory(
            organization=organization,
            branch=branch,
            current_section=other_section,
        )

    @pytest.fixture(autouse=True)
    def setup_assignment(
        self,
        organization,
        academic_year,
        subject,
        section,
        teacher,
    ):
        TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )

    def test_teacher_can_list_retrieve_and_update_logs_for_assigned_students(
        self,
        api_client,
        teacher,
        organization,
        student,
    ):
        log = InterventionLog.objects.create(
            organization=organization,
            student=student,
            intervention_type=InterventionLog.InterventionType.LOW_GRADE,
            severity=InterventionLog.Severity.MEDIUM,
            status=InterventionLog.Status.OPEN,
            title="Low grade alert",
            description="Needs review",
        )
        api_client.force_authenticate(user=teacher.user)

        list_response = api_client.get("/api/intervention-logs/")
        retrieve_response = api_client.get(f"/api/intervention-logs/{log.id}/")
        patch_response = api_client.patch(
            f"/api/intervention-logs/{log.id}/",
            {
                "status": InterventionLog.Status.IN_PROGRESS,
                "description": "Teacher is following up",
            },
            format="json",
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 1
        assert list_response.data["results"][0]["id"] == str(log.id)
        assert retrieve_response.status_code == status.HTTP_200_OK
        assert retrieve_response.data["id"] == str(log.id)
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.data["status"] == InterventionLog.Status.IN_PROGRESS

    def test_teacher_cannot_access_or_update_unassigned_logs(
        self,
        api_client,
        teacher,
        organization,
        other_student,
    ):
        log = InterventionLog.objects.create(
            organization=organization,
            student=other_student,
            intervention_type=InterventionLog.InterventionType.ATTENDANCE,
            severity=InterventionLog.Severity.HIGH,
            status=InterventionLog.Status.OPEN,
            title="Attendance concern",
            description="Too many absences",
        )
        api_client.force_authenticate(user=teacher.user)

        list_response = api_client.get("/api/intervention-logs/")
        retrieve_response = api_client.get(f"/api/intervention-logs/{log.id}/")
        patch_response = api_client.patch(
            f"/api/intervention-logs/{log.id}/",
            {"status": InterventionLog.Status.RESOLVED},
            format="json",
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 0
        assert retrieve_response.status_code == status.HTTP_404_NOT_FOUND
        assert patch_response.status_code == status.HTTP_404_NOT_FOUND
