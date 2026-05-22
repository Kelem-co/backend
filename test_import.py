import sys, os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from students.services.bulk_import import StudentBulkImportService
from organizations.models import Organization
from branches.models import Branch

with open("/home/robel/Desktop/Final Year Project/templates/student_import_test.csv", "rb") as f:
    content = f.read()

org = Organization.objects.first()
branch = Branch.objects.first()

service = StudentBulkImportService(
    file_content=content,
    file_name="student_import_test.csv",
    organization_id=org.id,
    branch_id=branch.id
)

success, errors = service.run()
print(f"Success: {success}")
print(f"Errors: {errors}")
