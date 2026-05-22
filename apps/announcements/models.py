from academics.models import Grade
from academics.models import Section
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class Announcement(UUIDModel, TimeStampedModel):
    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        SENT = "SENT", _("Sent")
        SCHEDULED = "SCHEDULED", _("Scheduled")

    class TargetRoleChoices(models.TextChoices):
        PARENTS = "PARENTS", _("Parents")
        TEACHERS = "TEACHERS", _("Teachers")
        BOTH = "BOTH", _("Both")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name=_("Branch"),
    )
    subject = models.CharField(_("Subject"), max_length=255)
    message = models.TextField(_("Message"))
    attachment = models.ForeignKey(
        "media.MediaFile",
        on_delete=models.SET_NULL,
        related_name="announcement_attachments",
        null=True,
        blank=True,
        verbose_name=_("Attachment"),
    )
    scheduled_at = models.DateTimeField(_("Scheduled At"), null=True, blank=True)
    is_urgent = models.BooleanField(_("Is Urgent"), default=False)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    target_roles = models.CharField(
        _("Target Roles"),
        max_length=20,
        choices=TargetRoleChoices.choices,
        default=TargetRoleChoices.BOTH,
    )

    class Meta:
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.branch.name})"


class AnnouncementGrade(UUIDModel, TimeStampedModel):
    """
    Junction table for targeting specific Grades with an announcement.
    """

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="targeted_grades",
        verbose_name=_("Announcement"),
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name=_("Grade"),
    )

    class Meta:
        verbose_name = _("Announcement Grade Target")
        verbose_name_plural = _("Announcement Grade Targets")
        unique_together = ("announcement", "grade")

    def __str__(self):
        return f"{self.announcement.subject} -> {self.grade.name}"


class AnnouncementSection(UUIDModel, TimeStampedModel):
    """
    Junction table for targeting specific Sections with an announcement.
    """

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="targeted_sections",
        verbose_name=_("Announcement"),
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name=_("Section"),
    )

    class Meta:
        verbose_name = _("Announcement Section Target")
        verbose_name_plural = _("Announcement Section Targets")
        unique_together = ("announcement", "section")

    def __str__(self):
        return f"{self.announcement.subject} -> {self.section.name}"
