import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDModel(models.Model):
    """
    Abstract base model that uses a UUID instead of a sequentially generated integer as its primary key.
    """  # noqa: E501

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract base model providing created_at and updated_at timestamp fields.
    """

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        abstract = True


class ImportJob(TimeStampedModel, UUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed")

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    task_id = models.CharField(
        _("Celery Task ID"),
        max_length=255,
        default="",
        blank=True,
    )
    file = models.ForeignKey(
        "media.MediaFile",
        on_delete=models.PROTECT,
        related_name="import_jobs",
        verbose_name=_("Uploaded File"),
    )
    module = models.CharField(
        _("Module"),
        max_length=50,
    )  # 'students', 'parents', 'teachers'
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="import_jobs",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="import_jobs",
    )
    errors = models.JSONField(_("Errors"), null=True, blank=True)
    progress = models.IntegerField(_("Progress"), default=0)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="import_jobs",
    )

    def __str__(self):
        return f"{self.module} import - {self.status}"
