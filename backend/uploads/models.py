from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class MediaFileStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    UPLOADED = "uploaded", _("Uploaded")
    FAILED = "failed", _("Failed")


class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=1024, unique=True)
    bucket = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.BigIntegerField(blank=True, null=True)
    etag = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=16,
        choices=MediaFileStatus,
        default=MediaFileStatus.PENDING,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="media_files",
    )
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key"], name="media_file_key_unique"),
        ]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.id})"


class UploadFingerprint(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True)
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        related_name="fingerprints",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.fingerprint
