from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class AcademicYear(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="academic_years",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="academic_years",
        verbose_name=_("Branch"),
    )
    name = models.CharField(_("Name"), max_length=100)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    is_current = models.BooleanField(_("Is Current"), default=False)

    class Meta:
        verbose_name = _("Academic Year")
        verbose_name_plural = _("Academic Years")
        unique_together = ("branch", "name")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class Grade(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Branch"),
    )
    name = models.CharField(_("Name"), max_length=100)
    level = models.IntegerField(_("Level"))

    class Meta:
        verbose_name = _("Grade")
        verbose_name_plural = _("Grades")
        unique_together = ("branch", "name")
        ordering = ["level"]

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class Section(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Branch"),
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Grade"),
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="sections",
        null=True,
        blank=True,
    )
    name = models.CharField(_("Name"), max_length=100)

    class Meta:
        verbose_name = _("Section")
        verbose_name_plural = _("Sections")
        unique_together = ("grade", "name", "academic_year")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.grade.name} - {self.name}"


class Subject(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Branch"),
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Grade"),
    )
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")
        unique_together = ("grade", "name")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.grade.name} - {self.name}"


class GradeSubject(UUIDModel, TimeStampedModel):
    """
    Junction table that records which subjects are offered for a given grade
    within a branch. This is the canonical source of truth for the curriculum
    structure; TeacherSubjectAssignment references it indirectly via Subject.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="grade_subjects",
        verbose_name=_("Organization"),
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="grade_subjects",
        verbose_name=_("Grade"),
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="grade_subjects",
        verbose_name=_("Subject"),
    )

    class Meta:
        verbose_name = _("Grade Subject")
        verbose_name_plural = _("Grade Subjects")
        unique_together = ("grade", "subject")
        ordering = ["grade__level", "subject__name"]

    def __str__(self):
        return f"{self.grade.name} — {self.subject.name}"


class CalendarDocument(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="calendar_documents",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="calendar_documents",
        verbose_name=_("Branch"),
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="calendar_documents",
        null=True,
        blank=True,
        verbose_name=_("Academic Year"),
    )
    media_file = models.ForeignKey(
        "media.MediaFile",
        on_delete=models.SET_NULL,
        related_name="calendar_documents",
        null=True,
        blank=True,
        verbose_name=_("Media File"),
    )

    class Meta:
        verbose_name = _("Calendar Document")
        verbose_name_plural = _("Calendar Documents")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "branch", "academic_year"],
                name="unique_calendar_document_per_scope",
            ),
        ]

    def __str__(self):
        academic_year_name = (
            self.academic_year.name if self.academic_year else "no year"
        )
        return f"{self.branch.name} - {academic_year_name}"
