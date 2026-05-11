from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class StatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    UPLOADED = "uploaded", "Uploaded"
    FAILED = "failed", "Failed"
    DELETED = "deleted", "Deleted"


class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(
        max_length=1024,
        unique=True,
        db_index=True,
        help_text="Object storage key (must be globally unique)",
    )
    bucket = models.CharField(
        max_length=63,
        db_index=True,
        help_text="S3/MinIO bucket name",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original file name (for display/download)",
    )
    content_type = models.CharField(
        max_length=127,
        help_text="MIME type (e.g., image/jpeg, application/pdf)",
    )
    size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes (set after upload confirmation)",
    )
    etag = models.CharField(  # noqa: DJ001
        max_length=255,
        null=True,
        blank=True,
        help_text="S3 ETag (set after upload confirmation)",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices,
        default=StatusChoices.PENDING,
        db_index=True,
        help_text="Current upload lifecycle status",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="media_files",
        help_text="User who initiated the upload",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when upload was initiated",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when upload status last changed",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uploaded_by", "-created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        verbose_name = "Media File"
        verbose_name_plural = "Media Files"

    def __str__(self) -> str:
        return f"{self.file_name} ({self.status})"

    def is_stale(self, ttl_seconds: int) -> bool:
        age = timezone.now() - self.created_at
        return age.total_seconds() > ttl_seconds


class UploadFingerprint(models.Model):
    fingerprint = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA256 hash of (user_id + file_name + content_type + time_window)",
    )
    media_file = models.OneToOneField(
        MediaFile,
        on_delete=models.CASCADE,
        related_name="fingerprint_record",
        help_text="MediaFile created by this fingerprinted request",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this fingerprint was recorded",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Upload Fingerprint"
        verbose_name_plural = "Upload Fingerprints"

    def __str__(self) -> str:
        return self.fingerprint
