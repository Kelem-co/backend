from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class Assessment(UUIDModel, TimeStampedModel):
    """
    A single graded task — Assignment, Exam, Quiz, or Homework.

    The TeacherSubjectAssignment FK gives us Section + Subject + Teacher +
    AcademicYear in one link, keeping the model fully normalised.
    """

    class TaskType(models.TextChoices):
        ASSIGNMENT = "ASSIGNMENT", _("Assignment")
        EXAM = "EXAM", _("Exam")
        QUIZ = "QUIZ", _("Quiz")
        HOMEWORK = "HOMEWORK", _("Homework")
        PROJECT = "PROJECT", _("Project")
        LAB = "LAB", _("Lab Work")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        PUBLISHED = "PUBLISHED", _("Published")
        CLOSED = "CLOSED", _("Closed")

    # ── Tenant isolation ─────────────────────────────────────────────────
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Branch"),
    )

    # ── Context: Section / Subject / Teacher / AcademicYear in one FK ───
    teacher_assignment = models.ForeignKey(
        "teachers.TeacherSubjectAssignment",
        on_delete=models.PROTECT,
        related_name="assessments",
        verbose_name=_("Teacher-Subject Assignment"),
        help_text=_(
            "Links this assessment to a specific Teacher, Subject, Section, "
            "and Academic Year — all derived from this single FK.",
        ),
    )

    # ── Assessment details ───────────────────────────────────────────────
    title = models.CharField(_("Title"), max_length=255)
    task_type = models.CharField(
        _("Task Type"),
        max_length=15,
        choices=TaskType.choices,
    )
    description = models.TextField(_("Description / Instructions"), blank=True)
    total_marks = models.DecimalField(
        _("Total Marks"),
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    passing_marks = models.DecimalField(
        _("Passing Marks"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(
            "Optional. If set, results below this value trigger an "
            "Intervention Required log in the analytics app.",
        ),
    )
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")
        ordering = ["-due_date", "title"]
        indexes = [
            models.Index(fields=["organization", "task_type"]),
            models.Index(fields=["teacher_assignment", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.get_task_type_display()}: {self.title} "
            f"({self.teacher_assignment.section.name})"
        )

    @property
    def section(self):
        return self.teacher_assignment.section

    @property
    def subject(self):
        return self.teacher_assignment.subject

    @property
    def teacher(self):
        return self.teacher_assignment.teacher

    @property
    def academic_year(self):
        return self.teacher_assignment.academic_year


class AssessmentResult(UUIDModel, TimeStampedModel):
    """
    One result row per student per assessment.
    Unique constraint: (assessment, student) — one result per student.
    """

    class SubmissionStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        SUBMITTED = "SUBMITTED", _("Submitted")
        LATE = "LATE", _("Late Submission")
        MISSING = "MISSING", _("Missing")
        GRADED = "GRADED", _("Graded")

    # ── Tenant isolation ─────────────────────────────────────────────────
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="assessment_results",
        verbose_name=_("Organization"),
    )

    # ── Core links ───────────────────────────────────────────────────────
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name=_("Assessment"),
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="assessment_results",
        verbose_name=_("Student"),
    )
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_results",
        verbose_name=_("Graded By"),
    )

    # ── Result data ───────────────────────────────────────────────────────
    obtained_marks = models.DecimalField(
        _("Obtained Marks"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    submission_status = models.CharField(
        _("Submission Status"),
        max_length=10,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    feedback = models.TextField(_("Teacher Feedback"), blank=True)

    # ── Homework-specific ─────────────────────────────────────────────────
    parent_confirmed = models.BooleanField(
        _("Parent Confirmed Completion"),
        default=False,
        help_text=_(
            "Set to True by the parent to confirm their child completed "
            "the homework. Relevant only when task_type=HOMEWORK.",
        ),
    )
    parent_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_homework_results",
        verbose_name=_("Confirmed By Parent"),
    )
    parent_confirmed_at = models.DateTimeField(
        _("Parent Confirmed At"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Assessment Result")
        verbose_name_plural = _("Assessment Results")
        unique_together = ("assessment", "student")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "submission_status"]),
            models.Index(fields=["student", "assessment"]),
        ]

    def __str__(self):
        marks = self.obtained_marks if self.obtained_marks is not None else "N/A"
        return (
            f"{self.student} | {self.assessment.title} | "
            f"{marks}/{self.assessment.total_marks}"
        )

    @property
    def percentage(self):
        if self.obtained_marks is None:
            return None
        return round(
            float(self.obtained_marks) / float(self.assessment.total_marks) * 100,
            2,
        )

    @property
    def is_below_passing(self):
        """
        True when the result is graded and below the assessment's
        passing_marks threshold.
        """
        pm = self.assessment.passing_marks
        if self.obtained_marks is None or pm is None:
            return False
        return self.obtained_marks < pm


class HomeworkConfirmation(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="homework_confirmations",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="homework_confirmations",
        verbose_name=_("Branch"),
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="homework_confirmations",
        verbose_name=_("Section"),
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="homework_confirmations",
        verbose_name=_("Assessment"),
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="homework_confirmations",
        verbose_name=_("Student"),
    )
    is_confirmed = models.BooleanField(_("Is Confirmed"), default=False)
    confirmed_at = models.DateTimeField(_("Confirmed At"), null=True, blank=True)
    feedback = models.TextField(_("Feedback"), blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homework_confirmations",
        verbose_name=_("Confirmed By"),
    )

    class Meta:
        verbose_name = _("Homework Confirmation")
        verbose_name_plural = _("Homework Confirmations")
        ordering = ["-created_at"]
        unique_together = ("assessment", "student")
        indexes = [
            models.Index(fields=["organization", "is_confirmed"]),
            models.Index(fields=["branch", "section"]),
            models.Index(fields=["assessment", "student"]),
        ]

    def __str__(self):
        return f"{self.student} | {self.assessment.title} | {self.is_confirmed}"

    def clean(self):
        super().clean()
        errors = {}

        if self.assessment_id and self.assessment.task_type != Assessment.TaskType.HOMEWORK:
            errors["assessment"] = _(
                "Homework confirmations are only valid for homework assessments.",
            )

        if self.assessment_id and self.student_id:
            if self.student.branch_id != self.assessment.branch_id:
                errors["student"] = _(
                    "Student must belong to the same branch as the assessment.",
                )
            if self.student.organization_id != self.assessment.organization_id:
                errors["student"] = _(
                    "Student must belong to the same organization as the assessment.",
                )
            if self.student.current_section_id != self.assessment.teacher_assignment.section_id:
                errors["student"] = _(
                    "Student must belong to the assessment's section.",
                )

        if self.organization_id and self.assessment_id:
            if self.organization_id != self.assessment.organization_id:
                errors["organization"] = _(
                    "Organization must match the assessment organization.",
                )

        if self.branch_id and self.assessment_id:
            if self.branch_id != self.assessment.branch_id:
                errors["branch"] = _("Branch must match the assessment branch.")

        if self.section_id and self.assessment_id:
            if self.section_id != self.assessment.teacher_assignment.section_id:
                errors["section"] = _(
                    "Section must match the assessment section.",
                )

        if errors:
            raise ValidationError(errors)
