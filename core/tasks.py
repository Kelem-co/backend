from celery import shared_task
from django.db import transaction
from core.models import ImportJob

@shared_task(bind=True)
def process_bulk_import(self, import_job_id):
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
    except ImportJob.DoesNotExist:
        return "ImportJob not found"

    import_job.status = ImportJob.Status.PROCESSING
    import_job.task_id = self.request.id
    import_job.save(update_fields=["status", "task_id"])

    # Determine which service to run
    service_class = None
    if import_job.module == 'students':
        from students.services.bulk_import import StudentBulkImportService
        service_class = StudentBulkImportService
    elif import_job.module == 'parents':
        from students.services.bulk_import import ParentBulkImportService
        service_class = ParentBulkImportService
    elif import_job.module == 'teachers':
        from teachers.services.bulk_import import TeacherBulkImportService
        service_class = TeacherBulkImportService
    else:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [{"row": 0, "errors": {"module": [f"Unknown module: {import_job.module}"]}}]
        import_job.save(update_fields=["status", "errors"])
        return "Failed - Unknown Module"

    file_content = import_job.file.read()
    file_name = import_job.file.name

    service = service_class(
        file_content=file_content,
        file_name=file_name,
        organization_id=import_job.organization_id,
        branch_id=import_job.branch_id
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
    except Exception as e:
        import_job.status = ImportJob.Status.FAILED
        import_job.errors = [{"row": 0, "errors": {"server": [f"Task error: {str(e)}"]}}]
        import_job.save(update_fields=["status", "errors"])

    return f"Completed: {import_job.status}"
