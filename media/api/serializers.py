from __future__ import annotations

import logging

from rest_framework import serializers

from media.models import MediaFile
from media.models import StatusChoices
from media.storage import S3StorageClient


class MediaFileReferenceField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        "not_uploaded": "Selected media file has not finished uploading.",
        "not_owned": "Selected media file does not belong to the current user.",
        "invalid_content_type": (
            "Selected media file must have content type {expected}."
        ),
    }

    def __init__(
        self,
        *args,
        content_type_prefix: str | None = None,
        **kwargs,
    ) -> None:
        kwargs.setdefault(
            "queryset",
            MediaFile.objects.select_related("uploaded_by"),
        )
        self.content_type_prefix = content_type_prefix
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        media = super().to_internal_value(data)
        request = self.context.get("request")

        if media.status != StatusChoices.UPLOADED:
            self.fail("not_uploaded")

        if (
            request is not None
            and getattr(request.user, "is_authenticated", False)
            and media.uploaded_by_id != request.user.id
        ):
            self.fail("not_owned")

        if self.content_type_prefix is not None and not media.content_type.startswith(
            self.content_type_prefix,
        ):
            self.fail(
                "invalid_content_type",
                expected=self.content_type_prefix,
            )

        return media


class UploadInitSerializer(serializers.Serializer):
    file_name = serializers.CharField(
        max_length=255,
        help_text="Original file name (will be sanitized)",
    )
    content_type = serializers.CharField(
        max_length=127,
        help_text="MIME type (e.g., image/jpeg)",
    )

    def validate_file_name(self, value: str) -> str:
        value = value.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1]
        value = value.strip()
        if not value:
            msg = "File name cannot be empty"
            raise serializers.ValidationError(msg)
        return value


class MediaFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

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
            "uploaded_by",
            "created_at",
            "updated_at",
            "download_url",
        ]
        read_only_fields = [
            "id",
            "key",
            "bucket",
            "size",
            "etag",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_download_url(self, obj: MediaFile) -> str | None:
        if obj.status != StatusChoices.UPLOADED:
            return None

        try:
            client = S3StorageClient()
            return client.get_download_url(obj.key)
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception(
                "Failed to generate download URL for media_id=%s",
                obj.id,
            )
            return None


class UploadResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    key = serializers.CharField()
    upload_id = serializers.CharField()
    expires_in = serializers.IntegerField()


class MultipartPartUrlRequestSerializer(serializers.Serializer):
    upload_id = serializers.CharField(max_length=255)
    part_number = serializers.IntegerField(min_value=1)


class MultipartPartUrlResponseSerializer(serializers.Serializer):
    presigned_url = serializers.CharField()
    expires_in = serializers.IntegerField()


class MultipartUploadPartSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(min_value=1)
    etag = serializers.CharField(max_length=255)


class MultipartCompleteRequestSerializer(serializers.Serializer):
    upload_id = serializers.CharField(max_length=255)
    parts = MultipartUploadPartSerializer(many=True, allow_empty=False)


class MultipartStatusResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    etag = serializers.CharField()
    size = serializers.IntegerField()


class MultipartAbortRequestSerializer(serializers.Serializer):
    upload_id = serializers.CharField(max_length=255)


class DownloadUrlResponseSerializer(serializers.Serializer):
    download_url = serializers.CharField()


class UploadResponseEnvelopeSerializer(serializers.Serializer):
    data = UploadResponseSerializer()


class MultipartPartUrlResponseEnvelopeSerializer(serializers.Serializer):
    data = MultipartPartUrlResponseSerializer()


class MultipartStatusResponseEnvelopeSerializer(serializers.Serializer):
    data = MultipartStatusResponseSerializer()


class MediaFileResponseEnvelopeSerializer(serializers.Serializer):
    data = MediaFileSerializer()


class DownloadUrlResponseEnvelopeSerializer(serializers.Serializer):
    data = DownloadUrlResponseSerializer()
