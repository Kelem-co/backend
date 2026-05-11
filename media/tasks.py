from __future__ import annotations

import logging

from celery import shared_task
from celery.schedules import crontab
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from config.celery_app import app
from media.models import MediaFile
from media.models import StatusChoices
from media.storage import S3StorageClient

logger = logging.getLogger(__name__)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0, hour="*"),
        cleanup_orphaned_uploads.s(),
        name="Cleanup orphaned uploads every hour",
    )


@shared_task(bind=True, max_retries=3)
def cleanup_orphaned_uploads(self) -> dict:
    settings_dict = settings.MEDIA_UPLOAD_SETTINGS
    ttl_seconds = settings_dict["UPLOAD_TTL"]

    threshold = timezone.now() - timezone.timedelta(seconds=ttl_seconds)
    orphaned_medias = MediaFile.objects.filter(
        status__in=[StatusChoices.PENDING, StatusChoices.FAILED, StatusChoices.DELETED],
        created_at__lt=threshold,
    )

    stats = {
        "deleted_from_storage": 0,
        "deleted_from_db": 0,
        "errors": [],
    }

    client = S3StorageClient()

    for media in orphaned_medias:
        try:
            with transaction.atomic():
                locked_media = MediaFile.objects.select_for_update().get(id=media.id)
                obj_info = client.head_object(locked_media.key)

                if obj_info["exists"]:
                    try:
                        client.delete_object(locked_media.key)
                        stats["deleted_from_storage"] += 1
                        logger.info(
                            "Deleted orphaned object: key=%s",
                            locked_media.key,
                        )
                    except Exception as exc:
                        logger.exception(
                            "Failed to delete object: key=%s",
                            locked_media.key,
                        )
                        stats["errors"].append(
                            {
                                "media_id": str(locked_media.id),
                                "type": "storage_deletion_failed",
                                "reason": str(exc),
                            },
                        )
                        raise

                media_id = locked_media.id
                locked_media.delete()
                stats["deleted_from_db"] += 1
                logger.info("Deleted orphaned record: media_id=%s", media_id)

        except Exception as exc:
            logger.exception(
                "Error processing orphaned media: media_id=%s",
                media.id,
            )
            stats["errors"].append(
                {
                    "media_id": str(media.id),
                    "type": "processing_error",
                    "reason": str(exc),
                },
            )

    logger.info(
        "Cleanup complete: deleted_from_storage=%s, deleted_from_db=%s, errors=%s",
        stats["deleted_from_storage"],
        stats["deleted_from_db"],
        len(stats["errors"]),
    )

    return stats
