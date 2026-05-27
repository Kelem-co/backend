import pytest
from academics.models import AcademicYear
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from students.api.views import ParentViewSet
from students.api.views import StudentViewSet
from students.models import Student
from students.models import StudentAcademicYearSection
from students.tests.factories import ParentFactory
from students.tests.factories import ParentStudentLinkFactory
from students.tests.factories import StudentAcademicYearSectionFactory
from students.tests.factories import StudentFactory
from teachers.models import HomeroomAssignment
from teachers.models import Teacher
from teachers.models import TeacherSubjectAssignment

from media.models import StatusChoices
from media.tests.factories import MediaFileFactory


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
        academic_year = AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            is_current=True,
        )
        grade = GradeFactory(organization=organization, branch=branch)
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )

    def test_student_crud(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)
        media = MediaFileFactory(
            uploaded_by=user,
            status=StatusChoices.UPLOADED,
            content_type="image/jpeg",
        )

        data = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "academic_year": str(section.academic_year_id),
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": "FEMALE",
            "date_of_birth": "2015-05-20",
            "roll_no": "R101",
            "current_section": str(section.id),
            "admission_date": "2023-09-01",
            "photo": str(media.id),
            "status": "ACTIVE",
        }
        response = api_client.post("/api/students/", data)
        assert response.status_code == status.HTTP_201_CREATED
        student_id = response.data["id"]
        assert str(response.data["photo"]) == str(media.id)
        assert StudentAcademicYearSection.objects.filter(
            student_id=student_id,
            academic_year=section.academic_year,
            section=section,
        ).exists()

        response = api_client.get("/api/students/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        response = api_client.get(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice"
        assert str(response.data["photo"]) == str(media.id)

        response = api_client.patch(
            f"/api/students/{student_id}/",
            {"first_name": "Alice Updated"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Alice Updated"

        response = api_client.delete(f"/api/students/{student_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_student_list_handles_student_without_current_section(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=None,
        )
        StudentAcademicYearSectionFactory(
            student=student,
            academic_year=AcademicYear.objects.get(
                organization=organization,
                branch=branch,
                is_current=True,
            ),
            section=None,
        )

        response = api_client.get(
            f"/api/students/?branch={branch.id}&organization={organization.id}",
        )

        assert response.status_code == status.HTTP_200_OK
        result = next(
            item for item in response.data["results"] if item["id"] == str(student.id)
        )
        assert result["current_section"] is None
        assert result["section_name"] is None
        assert result["grade_id"] is None
        assert result["grade_name"] is None
        assert result["grade_level"] is None
        assert result["academic_year_id"] is None
        assert result["academic_year_name"] is None

    def test_student_list_by_academic_year_includes_year_scoped_section(
        self,
        api_client,
        user,
        organization,
        branch,
        section,
    ):
        api_client.force_authenticate(user=user)
        student_with_section = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        StudentAcademicYearSectionFactory(
            student=student_with_section,
            academic_year=section.academic_year,
            section=section,
        )
        student_without_section = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=None,
        )
        StudentAcademicYearSectionFactory(
            student=student_without_section,
            academic_year=section.academic_year,
            section=None,
        )

        response = api_client.get(
            f"/api/students/?academic_year={section.academic_year_id}",
        )

        assert response.status_code == status.HTTP_200_OK
        results = {item["id"]: item for item in response.data["results"]}
        assert results[str(student_with_section.id)]["current_section"] == str(
            section.id,
        )
        assert results[str(student_with_section.id)]["academic_year_id"] == str(
            section.academic_year_id,
        )
        assert results[str(student_without_section.id)]["current_section"] is None
        assert results[str(student_without_section.id)]["academic_year_id"] == str(
            section.academic_year_id,
        )
        assert results[str(student_without_section.id)]["section_name"] is None

    def test_student_create_without_section_creates_year_mapping(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)
        academic_year = AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            is_current=True,
        )

        response = api_client.post(
            "/api/students/",
            {
                "organization": str(organization.id),
                "branch": str(branch.id),
                "academic_year": str(academic_year.id),
                "first_name": "No",
                "last_name": "Section",
                "gender": "MALE",
                "date_of_birth": "2015-05-20",
                "roll_no": "R102",
                "current_section": None,
                "admission_date": "2023-09-01",
                "status": "ACTIVE",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        student = Student.objects.get(id=response.data["id"])
        assert student.current_section is None
        assert StudentAcademicYearSection.objects.filter(
            student=student,
            academic_year=academic_year,
            section=None,
        ).exists()

    def test_student_patch_non_current_year_does_not_change_current_section(
        self,
        api_client,
        user,
        organization,
        branch,
        section,
    ):
        api_client.force_authenticate(user=user)
        non_current_year = AcademicYear.objects.create(
            organization=organization,
            branch=branch,
            name="2024/2025",
            start_date=section.academic_year.start_date,
            end_date=section.academic_year.end_date,
            is_current=False,
        )
        other_section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=section.grade,
            academic_year=non_current_year,
        )
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        StudentAcademicYearSectionFactory(
            student=student,
            academic_year=section.academic_year,
            section=section,
        )

        response = api_client.patch(
            f"/api/students/{student.id}/",
            {
                "academic_year": str(non_current_year.id),
                "current_section": str(other_section.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        student.refresh_from_db()
        assert student.current_section == section
        assert StudentAcademicYearSection.objects.filter(
            student=student,
            academic_year=non_current_year,
            section=other_section,
        ).exists()

    def test_student_patch_current_year_syncs_current_section(
        self,
        api_client,
        user,
        organization,
        branch,
        section,
    ):
        api_client.force_authenticate(user=user)
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=None,
        )
        StudentAcademicYearSectionFactory(
            student=student,
            academic_year=section.academic_year,
            section=None,
        )

        response = api_client.patch(
            f"/api/students/{student.id}/",
            {
                "academic_year": str(section.academic_year_id),
                "current_section": str(section.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        student.refresh_from_db()
        assert student.current_section == section
        assert StudentAcademicYearSection.objects.filter(
            student=student,
            academic_year=section.academic_year,
            section=section,
        ).exists()

    def test_student_list_by_academic_year_and_section_uses_year_scoped_mapping(
        self,
        api_client,
        user,
        organization,
        branch,
        section,
    ):
        api_client.force_authenticate(user=user)
        student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=None,
        )
        StudentAcademicYearSectionFactory(
            student=student,
            academic_year=section.academic_year,
            section=section,
        )

        response = api_client.get(
            f"/api/students/?academic_year={section.academic_year_id}&section={section.id}",
        )

        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data["results"]] == [str(student.id)]

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

    def test_teacher_can_list_students_for_assigned_section(self, api_client):
        teacher_user = UserFactory(role="TEACHER")
        organization = OrganizationFactory()
        branch = BranchFactory(school__organization=organization)
        academic_year = AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            name="2025/2026",
        )
        grade = GradeFactory(organization=organization, branch=branch)
        section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )
        other_section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )
        visible_student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        StudentFactory(
            organization=organization,
            branch=branch,
            current_section=other_section,
        )
        teacher = Teacher.objects.create(
            user=teacher_user,
            organization=organization,
            branch=branch,
            employee_id="EMP-STU-1",
            specialization="Mathematics",
        )
        subject = SubjectFactory(
            organization=organization,
            branch=branch,
            grade=grade,
        )
        TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=section,
            academic_year=academic_year,
        )
        api_client.force_authenticate(user=teacher_user)

        response = api_client.get(f"/api/students/by-section/?section={section.id}")

        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data] == [str(visible_student.id)]

    def test_teacher_cannot_list_students_for_unassigned_section(self, api_client):
        teacher_user = UserFactory(role="TEACHER")
        organization = OrganizationFactory()
        branch = BranchFactory(school__organization=organization)
        academic_year = AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            name="2025/2026",
        )
        grade = GradeFactory(organization=organization, branch=branch)
        assigned_section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )
        other_section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )
        StudentFactory(
            organization=organization,
            branch=branch,
            current_section=other_section,
        )
        teacher = Teacher.objects.create(
            user=teacher_user,
            organization=organization,
            branch=branch,
            employee_id="EMP-STU-2",
            specialization="English",
        )
        subject = SubjectFactory(
            organization=organization,
            branch=branch,
            grade=grade,
        )
        TeacherSubjectAssignment.objects.create(
            teacher=teacher,
            organization=organization,
            subject=subject,
            section=assigned_section,
            academic_year=academic_year,
        )
        api_client.force_authenticate(user=teacher_user)

        response = api_client.get(
            f"/api/students/by-section/?section={other_section.id}",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_homeroom_teacher_can_list_students_for_assigned_section(self, api_client):
        teacher_user = UserFactory(role="TEACHER")
        organization = OrganizationFactory()
        branch = BranchFactory(school__organization=organization)
        academic_year = AcademicYear.objects.get(
            organization=organization,
            branch=branch,
            name="2025/2026",
        )
        grade = GradeFactory(organization=organization, branch=branch)
        section = SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            academic_year=academic_year,
        )
        visible_student = StudentFactory(
            organization=organization,
            branch=branch,
            current_section=section,
        )
        teacher = Teacher.objects.create(
            user=teacher_user,
            organization=organization,
            branch=branch,
            employee_id="EMP-STU-3",
            specialization="Homeroom",
        )
        HomeroomAssignment.objects.create(
            organization=organization,
            branch=branch,
            academic_year=academic_year,
            section=section,
            teacher=teacher,
        )
        api_client.force_authenticate(user=teacher_user)

        response = api_client.get(f"/api/students/by-section/?section={section.id}")

        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data] == [str(visible_student.id)]

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
