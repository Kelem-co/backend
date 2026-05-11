from __future__ import annotations

import factory
from factory import Faker
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from media.models import MediaFile
from media.models import StatusChoices
from media.models import UploadFingerprint


class MediaFileFactory(DjangoModelFactory[MediaFile]):
    bucket = Faker("word")
    file_name = factory.Sequence(lambda n: f"test-file-{n:06d}.pdf")
    content_type = Faker("mime_type")
    size = Faker("pyint", min_value=1, max_value=1024)
    etag = Faker("uuid4")
    status = StatusChoices.UPLOADED
    uploaded_by = factory.SubFactory(UserFactory)
    key = factory.Sequence(lambda n: f"test-file-{n:06d}")

    class Meta:
        model = MediaFile


class UploadFingerprintFactory(DjangoModelFactory[UploadFingerprint]):
    fingerprint = Faker("sha256")
    media_file = factory.SubFactory(MediaFileFactory)

    class Meta:
        model = UploadFingerprint
