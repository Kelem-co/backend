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
            "email": ["johndoe@example.com", "janesmith@example.com"],
            "employee_id": ["EMP101", "EMP102"],
            "joining_date": ["2025-01-15", "2025-02-01"],
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
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["detail"] == "Teachers imported successfully."

        # Verify DB entries
        assert User.objects.filter(email="johndoe@example.com").exists()
        assert Teacher.objects.filter(employee_id="EMP101").exists()
        assert Teacher.objects.filter(employee_id="EMP102").exists()

    def test_teacher_bulk_import_excel_success(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        data = {
            "name": ["Robert Doe"],
            "email": ["robert@example.com"],
            "employee_id": ["EMP201"],
            "joining_date": ["2025-03-01"],
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
        assert response.status_code == status.HTTP_201_CREATED

        assert User.objects.filter(email="robert@example.com").exists()
        assert Teacher.objects.filter(employee_id="EMP201").exists()

    def test_teacher_bulk_import_validation_error(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        # First add a user with the email we will try to import to cause validation conflict
        UserFactory(email="duplicate@example.com")

        data = {
            "name": ["John Doe", "Jane Smith"],
            "email": ["duplicate@example.com", "janesmith2@example.com"],  # duplicate email
            "employee_id": ["EMP301", "EMP301"],  # duplicate employee id inside sheet
            "joining_date": ["invalid-date", "2025-02-01"],
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
        
        # Verify transaction rolled back (Jane Smith should not be created since row 1 had errors)
        assert not User.objects.filter(email="janesmith2@example.com").exists()
