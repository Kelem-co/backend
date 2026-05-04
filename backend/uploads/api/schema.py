from __future__ import annotations

from uuid import UUID

from ninja import ModelSchema
from ninja import Schema

from backend.uploads.models import MediaFile


class UploadInitSchema(Schema):
    file_name: str
    content_type: str


class UploadConfirmSchema(Schema):
    id: UUID
    size: int | None = None
    etag: str | None = None


class UploadInitResponseSchema(Schema):
    id: UUID
    key: str
    upload_url: str
    fields: dict[str, str]


class MediaUrlSchema(Schema):
    url: str


class MediaFileSchema(ModelSchema):
    class Meta:
        model = MediaFile
        fields = [
            "id",
            "key",
            "bucket",
            "file_name",
            "content_type",
            "size",
            "etag",
            "status",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
