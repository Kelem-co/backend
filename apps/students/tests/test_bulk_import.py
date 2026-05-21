import io
import pytest
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from academics.tests.factories import GradeFactory, SectionFactory
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchFactory
from organizations.tests.factories import OrganizationFactory
from students.models import Student, Parent, ParentStudentLink
from accounts.models import User

@pytest.mark.django_db
class TestStudentAndParentBulkImport:
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

    @pytest.fixture
    def section(self, organization, branch):
        grade = GradeFactory(organization=organization, branch=branch, name="Grade 9")
        return SectionFactory(
            organization=organization,
            branch=branch,
            grade=grade,
            name="Section A"
        )

    def test_parent_bulk_import_success(self, api_client, user, organization, branch):
        api_client.force_authenticate(user=user)

        data = {
            "name": ["Parent One", "Parent Two"],
            "father_name": ["FParent One", "FParent Two"],
            "grandfather_name": ["GParent One", "GParent Two"],
            "email": ["parent1@example.com", "parent2@example.com"],
            "phone_number": ["+251911111111", "+251911222222"],
            "secondary_phone_number": ["", "+251911333333"],
            "occupation": ["Merchant", "Doctor"],
        }
        df = pd.DataFrame(data)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        uploaded_file = SimpleUploadedFile(
            "parents.csv",
            csv_buf.getvalue().encode("utf-8"),
            content_type="text/csv"
        )

        payload = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "file": uploaded_file,
        }

        response = api_client.post("/api/parents/bulk-import/", payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED

        assert User.objects.filter(email="parent1@example.com", role=User.Role.PARENT).exists()
        assert Parent.objects.filter(user__email="parent1@example.com").exists()

    def test_student_bulk_import_success(self, api_client, user, organization, branch, section):
        api_client.force_authenticate(user=user)

        # Pre-create parent to test linking
        parent_user = UserFactory(email="parent@example.com", role=User.Role.PARENT)
        parent_profile = Parent.objects.create(user=parent_user)
        parent_profile.organizations.add(organization)
        parent_profile.branches.add(branch)

        data = {
            "first_name": ["Alice", "Bob"],
            "last_name": ["Green", "Brown"],
            "gender": ["FEMALE", "MALE"],
            "date_of_birth": ["2015-05-20", "2016-06-18"],
            "roll_no": ["R501", ""],
            "section_name": ["Section A", ""],
            "grade_name": ["Grade 9", ""],
            "admission_date": ["2023-09-01", ""],
            "parent_emails": ["parent@example.com", ""],
            "relationship_types": ["MOTHER", ""],
        }
        df = pd.DataFrame(data)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        uploaded_file = SimpleUploadedFile(
            "students.csv",
            csv_buf.getvalue().encode("utf-8"),
            content_type="text/csv"
        )

        payload = {
            "organization": str(organization.id),
            "branch": str(branch.id),
            "file": uploaded_file,
        }

        response = api_client.post("/api/students/bulk-import/", payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED

        assert Student.objects.filter(roll_no="R501", current_section=section).exists()
        assert Student.objects.filter(first_name="Bob", current_section=None).exists()
        
        # Verify parent links
        student_alice = Student.objects.get(roll_no="R501")
        assert ParentStudentLink.objects.filter(student=student_alice, parent=parent_profile, relationship_type="MOTHER").exists()
