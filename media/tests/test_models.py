from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.utils import timezone

from media.models import StatusChoices
from media.models import UploadFingerprint
from media.tests.factories import MediaFileFactory
from media.tests.factories import UploadFingerprintFactory

pytestmark = pytest.mark.django_db


class TestMediaFile:
    def test_create_media_file(self) -> None:
        media = MediaFileFactory()
        assert media.id is not None
        assert media.status == StatusChoices.UPLOADED
        assert media.file_name.startswith("test-file")

    def test_key_uniqueness(self) -> None:
        MediaFileFactory(key="unique-key-123")
        with pytest.raises(IntegrityError):
            MediaFileFactory(key="unique-key-123")

    def test_is_stale(self) -> None:
        old_media = MediaFileFactory()
        old_media.created_at = timezone.now() - timezone.timedelta(hours=2)
        old_media.save()

        fresh_media = MediaFileFactory()

        assert old_media.is_stale(ttl_seconds=3600)
        assert not fresh_media.is_stale(ttl_seconds=3600)


class TestUploadFingerprint:
    def test_create_fingerprint(self) -> None:
        fp = UploadFingerprintFactory()
        assert fp.fingerprint is not None
        assert fp.media_file is not None

    def test_fingerprint_uniqueness(self) -> None:
        media1 = MediaFileFactory()
        media2 = MediaFileFactory()
        UploadFingerprintFactory(fingerprint="unique-fp-123", media_file=media1)

        with pytest.raises(IntegrityError):
            UploadFingerprintFactory(fingerprint="unique-fp-123", media_file=media2)

    def test_fingerprint_cascade_delete(self) -> None:
        fp = UploadFingerprintFactory()
        media_id = fp.media_file.id

        fp.media_file.delete()

        with pytest.raises(UploadFingerprint.DoesNotExist):
            UploadFingerprint.objects.get(media_file_id=media_id)


class TestStatusChoices:
    def test_status_choices_values(self) -> None:
        assert StatusChoices.PENDING == "pending"
        assert StatusChoices.UPLOADED == "uploaded"
        assert StatusChoices.FAILED == "failed"
        assert StatusChoices.DELETED == "deleted"

    def test_media_default_status(self) -> None:
        media = MediaFileFactory(status=StatusChoices.PENDING)
        assert media.status == StatusChoices.PENDING
