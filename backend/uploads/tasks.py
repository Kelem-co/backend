from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from backend.uploads.models import MediaFile
from backend.uploads.models import MediaFileStatus
from backend.uploads.services import delete_object
from backend.uploads.services import head_object


@shared_task()
def cleanup_stale_pending_uploads() -> int:
    cutoff = timezone.now() - timedelta(hours=1)
    cleaned_up = 0

    stale_media = MediaFile.objects.filter(
        status=MediaFileStatus.PENDING,
        deleted_at__isnull=True,
        created_at__lt=cutoff,
    )
    for media_file in stale_media:
        try:
            head_object(media_file)
        except Exception:  # noqa: BLE001
            media_file.delete()
            cleaned_up += 1
            continue

        delete_object(media_file)
        with transaction.atomic():
            media_file.status = MediaFileStatus.FAILED
            media_file.save(update_fields=["status", "updated_at"])
        cleaned_up += 1

    return cleaned_up
