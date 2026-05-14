from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def notify_parent_of_absence(self, attendance_id: str):
    """
    Placeholder Celery task — triggered after an Attendance record is
    saved with status ABSENT or LATE.

    Replace the body with your actual notification logic:
      - Push notification via FCM/APNs
      - SMS via Twilio / Africa's Talking
      - In-app notification stored to a Notification model
    """
    try:
        from attendance.models import Attendance

        record = Attendance.objects.select_related(
            "student", "section", "student__parent_links__parent"
        ).get(id=attendance_id)

        # --- Notification logic placeholder ---
        # parents = record.student.parent_links.select_related("parent").all()
        # for link in parents:
        #     send_push(
        #         user=link.parent,
        #         title=f"Attendance Alert – {record.student.first_name}",
        #         body=(
        #             f"{record.student.first_name} was marked "
        #             f"{record.get_status_display()} on {record.date}. "
        #             "Please log in to provide a reason."
        #         ),
        #     )

        return {
            "status": "queued",
            "attendance_id": attendance_id,
            "triggered_at": timezone.now().isoformat(),
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def refresh_attendance_summary(self, student_id: str, academic_year_id: str):
    """
    Recomputes the AttendanceSummary row for one student/year combination.
    Called after every Attendance save via Django signal.
    """
    try:
        from attendance.models import Attendance, AttendanceSummary

        qs = Attendance.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id,
        )
        totals = {
            "total_present": qs.filter(status="PRESENT").count(),
            "total_absent": qs.filter(status="ABSENT").count(),
            "total_late": qs.filter(status="LATE").count(),
            "total_excused": qs.filter(status="EXCUSED").count(),
            "total_school_days": qs.count(),
        }

        # Fetch the first record to get organization FK
        first = qs.first()
        if first is None:
            return {"status": "no_records"}

        AttendanceSummary.objects.update_or_create(
            student_id=student_id,
            academic_year_id=academic_year_id,
            defaults={**totals, "organization": first.organization},
        )
        return {"status": "updated", "student_id": student_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
