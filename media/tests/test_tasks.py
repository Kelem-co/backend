from __future__ import annotations

from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone

from media.models import MediaFile
from media.models import StatusChoices
from media.tasks import cleanup_orphaned_uploads
from media.tests.factories import MediaFileFactory

pytestmark = pytest.mark.django_db


class TestCleanupOrphanedUploads:
    def test_cleanup_deletes_pending_uploads_older_than_ttl(self):
        old_media = MediaFileFactory(status=StatusChoices.PENDING)
        old_media.created_at = timezone.now() - timezone.timedelta(hours=2)
        old_media.save()

        fresh_media = MediaFileFactory(status=StatusChoices.PENDING)

        with mock.patch(
            "media.tasks.S3StorageClient.head_object",
        ) as mock_head:
            mock_head.return_value = {
                "exists": False,  # Object doesn't exist in storage
                "etag": None,
                "size": None,
                "content_type": None,
            }

            result = cleanup_orphaned_uploads()

        assert not MediaFile.objects.filter(id=old_media.id).exists()

        assert MediaFile.objects.filter(id=fresh_media.id).exists()

        assert result["deleted_from_db"] == 1
        assert result["deleted_from_storage"] == 0

    def test_cleanup_deletes_failed_uploads(self):
        failed_media = MediaFileFactory(status=StatusChoices.FAILED)
        failed_media.created_at = timezone.now() - timezone.timedelta(hours=2)
        failed_media.save()

        with mock.patch(
            "media.tasks.S3StorageClient.head_object",
        ) as mock_head:
            mock_head.return_value = {
                "exists": False,
                "etag": None,
                "size": None,
                "content_type": None,
            }

            result = cleanup_orphaned_uploads()

        assert not MediaFile.objects.filter(id=failed_media.id).exists()
        assert result["deleted_from_db"] == 1

    def test_cleanup_deletes_objects_from_storage(self):
        old_media = MediaFileFactory(status=StatusChoices.PENDING)
        old_media.created_at = timezone.now() - timezone.timedelta(hours=2)
        old_media.save()

        with (
            mock.patch(
                "media.tasks.S3StorageClient.head_object",
            ) as mock_head,
            mock.patch(
                "media.tasks.S3StorageClient.delete_object",
            ) as mock_delete,
        ):
            mock_head.return_value = {
                "exists": True,
                "etag": "abc123",
                "size": 1024,
                "content_type": "application/pdf",
            }

            result = cleanup_orphaned_uploads()

        mock_delete.assert_called_once_with(old_media.key)

        assert not MediaFile.objects.filter(id=old_media.id).exists()
        assert result["deleted_from_storage"] == 1
        assert result["deleted_from_db"] == 1

    def test_cleanup_respects_ttl_setting(self):
        very_old = MediaFileFactory(status=StatusChoices.PENDING)
        very_old.created_at = timezone.now() - timezone.timedelta(hours=3)
        very_old.save()

        slightly_old = MediaFileFactory(status=StatusChoices.PENDING)
        slightly_old.created_at = timezone.now() - timezone.timedelta(minutes=30)
        slightly_old.save()

        media_upload_settings = {
            **settings.MEDIA_UPLOAD_SETTINGS,
            "UPLOAD_TTL": 3600,
        }

        with (
            mock.patch(
                "media.tasks.settings.MEDIA_UPLOAD_SETTINGS",
                media_upload_settings,
            ),
            mock.patch(
                "media.tasks.S3StorageClient.head_object",
            ) as mock_head,
        ):
            mock_head.return_value = {
                "exists": False,
                "etag": None,
                "size": None,
                "content_type": None,
            }

            result = cleanup_orphaned_uploads()

        assert not MediaFile.objects.filter(id=very_old.id).exists()
        assert MediaFile.objects.filter(id=slightly_old.id).exists()
        assert result["deleted_from_db"] == 1

    def test_cleanup_handles_errors_gracefully(self):
        old_media1 = MediaFileFactory(status=StatusChoices.PENDING)
        old_media1.created_at = timezone.now() - timezone.timedelta(hours=2)
        old_media1.save()

        old_media2 = MediaFileFactory(status=StatusChoices.PENDING)
        old_media2.created_at = timezone.now() - timezone.timedelta(hours=3)
        old_media2.save()

        with mock.patch(
            "media.tasks.S3StorageClient.head_object",
        ) as mock_head:
            mock_head.side_effect = [
                Exception("Connection error"),
                {
                    "exists": False,
                    "etag": None,
                    "size": None,
                    "content_type": None,
                },
            ]

            result = cleanup_orphaned_uploads()

        assert len(result["errors"]) == 1
        assert "Connection error" in result["errors"][0]["reason"]

        assert MediaFile.objects.filter(id=old_media1.id).exists()
        assert not MediaFile.objects.filter(id=old_media2.id).exists()

    def test_cleanup_ignores_recent_uploads(self):
        recent_media = MediaFileFactory(status=StatusChoices.PENDING)

        with mock.patch("media.tasks.S3StorageClient.head_object"):
            result = cleanup_orphaned_uploads()

        assert MediaFile.objects.filter(id=recent_media.id).exists()
        assert result["deleted_from_db"] == 0
