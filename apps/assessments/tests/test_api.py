from datetime import date

import pytest
from academics.models import AcademicYear
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from accounts.tests.factories import UserFactory
from assessments.models import Assessment
from assessments.models import AssessmentResult
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from students.tests.factories import StudentFactory
from teachers.models import Teacher
from teachers.models import TeacherSubjectAssignment


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

    def test_teacher_can_fetch_own_assessments_by_filters(  # noqa: PLR0913
        self,
        api_client,
        organization,
        branch,
        academic_year,
        section,
        subject,
        teacher,
    ):
        api_client.force_authenticate(user=teacher.user)

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
            title="Teacher Visible Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=25,
            passing_marks=12,
            due_date=date(2026, 1, 20),
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
            title="Teacher Hidden Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=25,
            passing_marks=12,
            due_date=date(2026, 1, 21),
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
        assert response.data["results"][0]["teacher_name"] == "Abel"


@pytest.mark.django_db
class TestAssessmentResultsTeacherAccessAPI:
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
        return GradeFactory(
            organization=organization,
            branch=branch,
            name="Grade 8",
            level=8,
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
        return SubjectFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            name="Physics",
            code="PHY-8",
        )

    @pytest.fixture
    def teacher(self, organization, branch):
        return Teacher.objects.create(
            user=UserFactory(role="TEACHER", name="Assigned Teacher"),
            organization=organization,
            branch=branch,
            employee_id="EMP-AR-1",
            specialization="Physics",
        )

    @pytest.fixture
    def other_teacher(self, organization, branch):
        return Teacher.objects.create(
            user=UserFactory(role="TEACHER", name="Other Teacher"),
            organization=organization,
            branch=branch,
            employee_id="EMP-AR-2",
            specialization="Chemistry",
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

    @pytest.fixture
    def assessment(  # noqa: PLR0913
        self,
        organization,
        branch,
        academic_year,
        section,
        subject,
        teacher,
    ):
        assignment = TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )
        return Assessment.objects.create(
            organization=organization,
            branch=branch,
            teacher_assignment=assignment,
            title="Assigned Teacher Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=20,
            passing_marks=10,
            due_date=date(2026, 2, 1),
            status=Assessment.Status.PUBLISHED,
        )

    @pytest.fixture
    def other_assessment(  # noqa: PLR0913
        self,
        organization,
        branch,
        academic_year,
        other_section,
        subject,
        other_teacher,
    ):
        assignment = TeacherSubjectAssignment.objects.create(
            teacher=other_teacher,
            organization=organization,
            subject=subject,
            section=other_section,
            academic_year=academic_year,
        )
        return Assessment.objects.create(
            organization=organization,
            branch=branch,
            teacher_assignment=assignment,
            title="Other Teacher Quiz",
            task_type=Assessment.TaskType.QUIZ,
            total_marks=20,
            passing_marks=10,
            due_date=date(2026, 2, 2),
            status=Assessment.Status.PUBLISHED,
        )

    def test_assigned_teacher_can_read_results_for_own_assessment(
        self,
        api_client,
        teacher,
        assessment,
        student,
    ):
        result = AssessmentResult.objects.create(
            organization=assessment.organization,
            assessment=assessment,
            student=student,
            submission_status=AssessmentResult.SubmissionStatus.GRADED,
            obtained_marks=18,
        )
        api_client.force_authenticate(user=teacher.user)

        list_response = api_client.get(
            "/api/assessment-results/",
            {"assessment": str(assessment.id)},
        )
        by_assessment_response = api_client.get(
            "/api/assessment-results/by-assessment/",
            {"assessment": str(assessment.id)},
        )
        by_student_response = api_client.get(
            "/api/assessment-results/by-student/",
            {"student": str(student.id)},
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 1
        assert list_response.data["results"][0]["id"] == str(result.id)
        assert by_assessment_response.status_code == status.HTTP_200_OK
        assert by_assessment_response.data[0]["id"] == str(result.id)
        assert by_student_response.status_code == status.HTTP_200_OK
        assert by_student_response.data[0]["id"] == str(result.id)

    def test_assigned_teacher_can_create_and_bulk_grade_own_results(
        self,
        api_client,
        teacher,
        assessment,
        student,
    ):
        api_client.force_authenticate(user=teacher.user)

        create_response = api_client.post(
            "/api/assessment-results/",
            {
                "organization": str(assessment.organization_id),
                "assessment": str(assessment.id),
                "student": str(student.id),
                "obtained_marks": "15.00",
                "submission_status": AssessmentResult.SubmissionStatus.GRADED,
                "feedback": "Good work",
            },
            format="json",
        )
        bulk_response = api_client.post(
            "/api/assessment-results/bulk-grade/",
            {
                "assessment": str(assessment.id),
                "results": [
                    {
                        "student": str(student.id),
                        "obtained_marks": "16.00",
                        "submission_status": AssessmentResult.SubmissionStatus.GRADED,
                        "feedback": "Updated",
                    },
                ],
            },
            format="json",
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        assert create_response.data["graded_by"] == teacher.user.id
        assert bulk_response.status_code == status.HTTP_200_OK
        assert bulk_response.data["updated"] == 1

    def test_teacher_cannot_read_or_write_other_teachers_results(  # noqa: PLR0913
        self,
        api_client,
        teacher,
        other_assessment,
        other_student,
        organization,
        branch,
        other_section,
    ):
        foreign_result = AssessmentResult.objects.create(
            organization=other_assessment.organization,
            assessment=other_assessment,
            student=other_student,
            submission_status=AssessmentResult.SubmissionStatus.GRADED,
            obtained_marks=11,
        )
        another_other_student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=other_section,
        )
        api_client.force_authenticate(user=teacher.user)

        list_response = api_client.get(
            "/api/assessment-results/",
            {"assessment": str(other_assessment.id)},
        )
        by_assessment_response = api_client.get(
            "/api/assessment-results/by-assessment/",
            {"assessment": str(other_assessment.id)},
        )
        create_response = api_client.post(
            "/api/assessment-results/",
            {
                "organization": str(other_assessment.organization_id),
                "assessment": str(other_assessment.id),
                "student": str(another_other_student.id),
                "obtained_marks": "9.00",
                "submission_status": AssessmentResult.SubmissionStatus.GRADED,
            },
            format="json",
        )
        bulk_response = api_client.post(
            "/api/assessment-results/bulk-grade/",
            {
                "assessment": str(other_assessment.id),
                "results": [
                    {
                        "student": str(other_student.id),
                        "obtained_marks": "9.00",
                        "submission_status": AssessmentResult.SubmissionStatus.GRADED,
                    },
                ],
            },
            format="json",
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] == 0
        assert by_assessment_response.status_code == status.HTTP_200_OK
        assert by_assessment_response.data == []
        assert create_response.status_code == status.HTTP_403_FORBIDDEN
        assert bulk_response.status_code == status.HTTP_403_FORBIDDEN
        assert AssessmentResult.objects.filter(id=foreign_result.id).exists()
