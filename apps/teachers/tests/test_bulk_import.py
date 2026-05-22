import io
import pytest
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from teachers.models import Teacher
from accounts.models import User

@pytest.mark.django_db
class TestTeacherBulkImport:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return UserFactory(is_superuser=True)

    @pytest.fixture
    def organization(self, user):
        return OrganizationFactory(owner=user)

    @pytest.fixture
    def branch(self, organization):
        return BranchFactory(school__organization=organization)

    def test_teacher_bulk_import_csv_success(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        data = {
            "name": ["John Doe", "Jane Smith"],
            "father_name": ["Richard Doe", "William Smith"],
            "grandfather_name": ["Robert Doe", "James Smith"],
            "email": ["johndoe@example.com", "janesmith@example.com"],
            "phone_number": ["+251911111111", "+251922222222"],
            "specialization": ["Math", "Physics"],
            "bio": ["Math teacher bio", "Physics teacher bio"],
        }
        df = pd.DataFrame(data)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        uploaded_file = SimpleUploadedFile(
            "teachers.csv",
            csv_buf.getvalue().encode("utf-8"),
            content_type="text/csv"
        )

        payload = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "file": uploaded_file,
        }

        response = api_client.post("/api/teachers/bulk-import/", payload, format="multipart")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["detail"] == "Bulk import process started."

        # Verify DB entries
        assert User.objects.filter(email="johndoe@example.com").exists()
        assert Teacher.objects.filter(user__email="johndoe@example.com").exists()
        assert Teacher.objects.filter(user__email="janesmith@example.com").exists()

    def test_teacher_bulk_import_excel_success(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        data = {
            "name": ["Robert Doe"],
            "father_name": ["Richard Doe"],
            "grandfather_name": ["William Doe"],
            "email": ["robert@example.com"],
            "phone_number": ["+251933333333"],
            "specialization": ["Biology"],
            "bio": ["Biology teacher"],
        }
        df = pd.DataFrame(data)
        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False)
        uploaded_file = SimpleUploadedFile(
            "teachers.xlsx",
            excel_buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        payload = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "file": uploaded_file,
        }

        response = api_client.post("/api/teachers/bulk-import/", payload, format="multipart")
        assert response.status_code == status.HTTP_202_ACCEPTED

        assert User.objects.filter(email="robert@example.com").exists()
        assert Teacher.objects.filter(user__email="robert@example.com").exists()

    def test_teacher_bulk_import_validation_error(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        # First add a user with the email we will try to import to cause validation conflict
        UserFactory(email="duplicate@example.com")

        data = {
            "name": ["John Doe", "Jane Smith"],
            "father_name": ["Richard Doe", "William Smith"],
            "grandfather_name": ["Robert Doe", "James Smith"],
            "email": ["duplicate@example.com", "janesmith2@example.com"],  # duplicate email
            "phone_number": ["+251944444444", "+251944444444"],  # duplicate phone inside sheet
        }
        df = pd.DataFrame(data)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        uploaded_file = SimpleUploadedFile(
            "teachers_error.csv",
            csv_buf.getvalue().encode("utf-8"),
            content_type="text/csv"
        )

        payload = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "file": uploaded_file,
        }

        response = api_client.post("/api/teachers/bulk-import/", payload, format="multipart")
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Verify transaction rolled back (Jane Smith should not be created since row 1 had errors)
        assert not User.objects.filter(email="janesmith2@example.com").exists()
        
        # Verify the import job failed
        from core.models import ImportJob
        job = ImportJob.objects.last()
        assert job.status == ImportJob.Status.FAILED
        assert job.errors is not None
        
        # Verify transaction rolled back (Jane Smith should not be created since row 1 had errors)
        assert not User.objects.filter(email="janesmith2@example.com").exists()
