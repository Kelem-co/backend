import os
from pathlib import Path

import django
from branches.models import Branch
from organizations.models import Organization
from students.services.bulk_import import StudentBulkImportService

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()


with Path.open(
    "/home/robel/Desktop/Final Year Project/templates/student_import_test.csv",
    "rb",
) as f:
    content = f.read()

org = Organization.objects.first()
branch = Branch.objects.first()

service = StudentBulkImportService(
    file_content=content,
    file_name="student_import_test.csv",
    organization_id=org.id,
    branch_id=branch.id,
)

success, errors = service.run()
RESULT = {
    "success": success,
    "errors": errors,
}
