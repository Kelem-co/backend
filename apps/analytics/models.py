from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class InterventionLog(UUIDModel, TimeStampedModel):
    """
    Stores any system-detected event that requires staff follow-up.

    Currently populated by:
      - Assessment signals when a student's grade falls below threshold.

    Future sources:
      - Attendance signals (e.g., > N consecutive absences).
      - Behaviour events, counsellor referrals, etc.
    """

    class InterventionType(models.TextChoices):
        LOW_GRADE = "LOW_GRADE", _("Low Grade")
        ATTENDANCE = "ATTENDANCE", _("Attendance Concern")
        BEHAVIOUR = "BEHAVIOUR", _("Behaviour Concern")
        OTHER = "OTHER", _("Other")

    class Severity(models.TextChoices):
        LOW = "LOW", _("Low")
        MEDIUM = "MEDIUM", _("Medium")
        HIGH = "HIGH", _("High")
        CRITICAL = "CRITICAL", _("Critical")

    class Status(models.TextChoices):
        OPEN = "OPEN", _("Open")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        RESOLVED = "RESOLVED", _("Resolved")
        DISMISSED = "DISMISSED", _("Dismissed")

    # ── Tenant isolation ─────────────────────────────────────────────────
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="intervention_logs",
        verbose_name=_("Organization"),
    )

    # ── Who is this about ────────────────────────────────────────────────
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="intervention_logs",
        verbose_name=_("Student"),
    )

    # ── Classification ───────────────────────────────────────────────────
    intervention_type = models.CharField(
        _("Intervention Type"),
        max_length=20,
        choices=InterventionType.choices,
        default=InterventionType.LOW_GRADE,
    )
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=Status.choices,
        default=Status.OPEN,
    )

    # ── Context (generic FK pattern without ContentTypes overhead) ───────
    # Store the source model name + id so the log can point back to the
    # triggering record (e.g., AssessmentResult, Attendance, etc.)
    source_model = models.CharField(
        _("Source Model"),
        max_length=100,
        blank=True,
        help_text=_("e.g. 'assessments.AssessmentResult'"),
    )
    source_id = models.UUIDField(
        _("Source ID"),
        null=True,
        blank=True,
        help_text=_("PK of the triggering record."),
    )

    # ── Human-readable context ───────────────────────────────────────────
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Intervention Log")
        verbose_name_plural = _("Intervention Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["student", "intervention_type"]),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title} — {self.student}"
