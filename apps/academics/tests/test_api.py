import pytest
from academics.models import CalendarDocument
from academics.tests.factories import AcademicYearFactory
from academics.tests.factories import CalendarDocumentFactory
from academics.tests.factories import GradeFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APIClient

from media.tests.factories import MediaFileFactory


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
            "is_current": True,
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
        response = api_client.patch(
            f"/api/academic-years/{year_id}/",
            {"name": "2024/25 UPDATED"},
        )
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
            "level": 10,
        }
        response = api_client.post("/api/grades/", data)
        assert response.status_code == status.HTTP_201_CREATED
        grade_id = response.data["id"]

        # List
        response = api_client.get("/api/grades/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # Update
        response = api_client.patch(
            f"/api/grades/{grade_id}/",
            {"name": "Grade 10 Updated"},
        )
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
            "name": "Section A",
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
            "code": "MATH101",
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

    def test_get_current_calendar_document(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)
        media_file = MediaFileFactory(
            uploaded_by=user,
            content_type="application/pdf",
        )
        document = CalendarDocumentFactory(
            organization=organization,
            branch=branch,
            media_file=media_file,
        )

        response = api_client.get(
            "/api/calendar-documents/current/",
            {
                "branch": str(branch.id),
                "organization": str(organization.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(document.id)
        assert response.data["media_file"] == str(media_file.id)
        assert response.data["file_name"] == media_file.file_name
        assert response.data["academic_year"] is None

    def test_get_current_calendar_document_returns_404_when_missing(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            "/api/calendar-documents/current/",
            {
                "branch": str(branch.id),
                "organization": str(organization.id),
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_current_calendar_document_creates_and_updates(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)
        first_media_file = MediaFileFactory(
            uploaded_by=user,
            content_type="application/pdf",
        )
        second_media_file = MediaFileFactory(
            uploaded_by=user,
            content_type="application/pdf",
        )
        academic_year = AcademicYearFactory(
            organization=organization,
            branch=branch,
        )

        create_response = api_client.post(
            "/api/calendar-documents/current/",
            {
                "media_file": str(first_media_file.id),
                "branch": str(branch.id),
                "organization": str(organization.id),
                "academic_year": str(academic_year.id),
            },
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        created_id = create_response.data["id"]
        assert create_response.data["media_file"] == str(first_media_file.id)
        assert CalendarDocument.objects.count() == 1

        update_response = api_client.post(
            "/api/calendar-documents/current/",
            {
                "media_file": str(second_media_file.id),
                "branch": str(branch.id),
                "organization": str(organization.id),
                "academic_year": str(academic_year.id),
            },
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data["id"] == created_id
        assert update_response.data["media_file"] == str(second_media_file.id)
        assert CalendarDocument.objects.count() == 1

    def test_branch_admin_can_manage_current_calendar_document(
        self,
        api_client,
        organization,
        branch,
    ):
        branch_admin = BranchAdminFactory(branch=branch, organization=organization)
        api_client.force_authenticate(user=branch_admin.user)
        media_file = MediaFileFactory(
            uploaded_by=branch_admin.user,
            content_type="application/pdf",
        )

        response = api_client.post(
            "/api/calendar-documents/current/",
            {
                "media_file": str(media_file.id),
                "branch": str(branch.id),
                "organization": str(organization.id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_post_current_calendar_document_rejects_non_pdf(
        self,
        api_client,
        user,
        organization,
        branch,
    ):
        api_client.force_authenticate(user=user)
        media_file = MediaFileFactory(
            uploaded_by=user,
            content_type="image/png",
        )

        response = api_client.post(
            "/api/calendar-documents/current/",
            {
                "media_file": str(media_file.id),
                "branch": str(branch.id),
                "organization": str(organization.id),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["errors"][0]["field"] == "media_file"
