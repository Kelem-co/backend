from celery import shared_task
from django.db import DatabaseError
from students.services.bulk_import import ParentBulkImportService
from students.services.bulk_import import StudentBulkImportService
from teachers.services.bulk_import import TeacherBulkImportService

from core.models import ImportJob
from media.storage import S3StorageClient

SERVICE_BY_MODULE = {
    "students": StudentBulkImportService,
    "parents": ParentBulkImportService,
    "teachers": TeacherBulkImportService,
}


@shared_task(bind=True)
def process_bulk_import(self, import_job_id):
    try:
        import_job = ImportJob.objects.select_related("file").get(id=import_job_id)
    except ImportJob.DoesNotExist:
        return "ImportJob not found"

    import_job.status = ImportJob.Status.PROCESSING
    import_job.task_id = self.request.id
    import_job.save(update_fields=["status", "task_id"])

    service_class = SERVICE_BY_MODULE.get(import_job.module)
    if service_class is None:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [
            {"row": 0, "errors": {"module": [f"Unknown module: {import_job.module}"]}},
        ]
        import_job.save(update_fields=["status", "errors"])
        return "Failed - Unknown Module"

    storage_client = S3StorageClient()
    file_content = storage_client.get_object_bytes(import_job.file.key)
    file_name = import_job.file.file_name

    service = service_class(
        file_content=file_content,
        file_name=file_name,
        organization_id=import_job.organization_id,
        branch_id=import_job.branch_id,
        current_section=import_job.current_section,
    )

    try:
        success, errors = service.run()
    except (DatabaseError, OSError, TypeError, ValueError) as e:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [{"row": 0, "errors": {"server": [f"Task error: {e!s}"]}}]
        import_job.save(update_fields=["status", "errors"])
        return f"Completed: {import_job.status}"

    if success:
        import_job.status = ImportJob.Status.SUCCESS
        import_job.progress = 100
    else:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = errors
    import_job.save(update_fields=["status", "progress", "errors"])

    return f"Completed: {import_job.status}"
