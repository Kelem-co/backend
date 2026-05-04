from __future__ import annotations

import uuid

from factory import Faker
from factory import SubFactory
from factory.django import DjangoModelFactory

from backend.uploads.models import MediaFile
from backend.uploads.models import MediaFileStatus
from backend.users.tests.factories import UserFactory


class MediaFileFactory(DjangoModelFactory[MediaFile]):
    key = Faker("uuid4")
    bucket = "media"
    file_name = Faker("file_name")
    content_type = "image/png"
    status = MediaFileStatus.PENDING
    uploaded_by = SubFactory(UserFactory)

    class Meta:
        model = MediaFile

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if "key" not in kwargs:
            kwargs["key"] = f"uploads/1/{uuid.uuid4()}.png"
        return super()._create(model_class, *args, **kwargs)
