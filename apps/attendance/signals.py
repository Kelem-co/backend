from attendance.models import Attendance
from attendance.tasks import notify_parent_of_absence
from attendance.tasks import refresh_attendance_summary
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Attendance)
def on_attendance_saved(sender, instance: Attendance, **kwargs):
    """
    After every Attendance save:
      1. Fire a parent notification if the student is ABSENT or LATE.
      2. Recompute the AttendanceSummary for that student/year.

    Tasks are queued asynchronously so the HTTP response is never delayed.
    """

    # Only notify on relevant statuses
    if instance.status in (
        Attendance.Status.ABSENT,
        Attendance.Status.LATE,
    ):
        notify_parent_of_absence.delay(str(instance.id))

    # Always keep the summary fresh
    refresh_attendance_summary.delay(
        str(instance.student_id),
        str(instance.academic_year_id),
    )
