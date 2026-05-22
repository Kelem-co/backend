from celery import shared_task
from students.services.bulk_import import ParentBulkImportService
from students.services.bulk_import import StudentBulkImportService
from teachers.services.bulk_import import TeacherBulkImportService

from core.models import ImportJob

SERVICE_BY_MODULE = {
    "students": StudentBulkImportService,
    "parents": ParentBulkImportService,
    "teachers": TeacherBulkImportService,
}


@shared_task(bind=True)
def process_bulk_import(self, import_job_id):
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
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

    file_content = import_job.file.read()
    file_name = import_job.file.name

    service = service_class(
        file_content=file_content,
        file_name=file_name,
        organization_id=import_job.organization_id,
        branch_id=import_job.branch_id,
    )

    try:
        success, errors = service.run()
        if success:
            import_job.status = ImportJob.Status.SUCCESS
            import_job.progress = 100
        else:
            import_job.status = ImportJob.Status.FAILED
            import_job.errors = errors
        import_job.save(update_fields=["status", "progress", "errors"])
    except Exception as e:  # noqa: BLE001
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [{"row": 0, "errors": {"server": [f"Task error: {e!s}"]}}]
        import_job.save(update_fields=["status", "errors"])

    return f"Completed: {import_job.status}"
