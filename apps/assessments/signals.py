from django.db.models.signals import post_save
from django.dispatch import receiver

from assessments.models import AssessmentResult


@receiver(post_save, sender=AssessmentResult)
def check_intervention_threshold(sender, instance: AssessmentResult, created: bool, **kwargs):
    """
    After every AssessmentResult save, check if the student's marks
    fall below the passing threshold. If so, create or update an
    InterventionLog entry in the analytics app.

    Logic:
      - Only triggers when obtained_marks is set (i.e., GRADED status).
      - Uses get_or_create so repeated saves don't duplicate logs.
      - Severity scales with how far below passing the student is:
          < 50 % of passing → HIGH
          50–79 % of passing → MEDIUM
          ≥ 80 % of passing → LOW
    """
    if not instance.is_below_passing:
        return

    from analytics.models import InterventionLog

    assessment = instance.assessment
    obtained = float(instance.obtained_marks)
    passing = float(assessment.passing_marks)
    ratio = obtained / passing  # < 1.0 since is_below_passing is True

    if ratio < 0.50:
        severity = InterventionLog.Severity.HIGH
    elif ratio < 0.80:
        severity = InterventionLog.Severity.MEDIUM
    else:
        severity = InterventionLog.Severity.LOW

    title = (
        f"Low Grade Alert: {instance.student.first_name} {instance.student.last_name} "
        f"scored {instance.obtained_marks}/{assessment.total_marks} on '{assessment.title}'"
    )
    description = (
        f"Student obtained {instance.percentage}% "
        f"(passing threshold: {assessment.passing_marks}/{assessment.total_marks}). "
        f"Subject: {assessment.subject.name} | "
        f"Section: {assessment.section.name} | "
        f"Teacher: {assessment.teacher.user.name}"
    )

    # get_or_create keyed on (student, source_id) so reruns are idempotent
    InterventionLog.objects.get_or_create(
        student=instance.student,
        source_id=instance.id,
        defaults={
            "organization": instance.organization,
            "intervention_type": InterventionLog.InterventionType.LOW_GRADE,
            "severity": severity,
            "status": InterventionLog.Status.OPEN,
            "source_model": "assessments.AssessmentResult",
            "title": title,
            "description": description,
        },
    )
