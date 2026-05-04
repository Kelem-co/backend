from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.db import IntegrityError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from backend.uploads.api.schema import MediaFileSchema
from backend.uploads.api.schema import MediaUrlSchema
from backend.uploads.api.schema import UploadConfirmSchema
from backend.uploads.api.schema import UploadInitResponseSchema
from backend.uploads.api.schema import UploadInitSchema
from backend.uploads.models import MediaFile
from backend.uploads.models import MediaFileStatus
from backend.uploads.models import UploadFingerprint
from backend.uploads.services import build_media_key
from backend.uploads.services import build_upload_fingerprint
from backend.uploads.services import delete_object
from backend.uploads.services import generate_presigned_get_url
from backend.uploads.services import generate_presigned_post
from backend.uploads.services import head_object
from backend.uploads.services import normalize_file_name
from backend.uploads.services import validate_content_type

router = Router(tags=["uploads"])


def _media_queryset(request):
    return MediaFile.objects.filter(uploaded_by=request.user, deleted_at__isnull=True)


def _build_init_response(media_file: MediaFile) -> UploadInitResponseSchema:
    upload = generate_presigned_post(media_file)
    return UploadInitResponseSchema(
        id=media_file.id,
        key=media_file.key,
        upload_url=upload["url"],
        fields={key: str(value) for key, value in upload["fields"].items()},
    )


def _ensure_media_file_for_init(request, data: UploadInitSchema) -> MediaFile:
    validate_content_type(data.content_type)
    fingerprint = build_upload_fingerprint(
        request.user.pk,
        data.file_name,
        data.content_type,
    )
    try:
        fingerprint_obj = UploadFingerprint.objects.select_related("media_file").get(
            fingerprint=fingerprint,
        )
        return fingerprint_obj.media_file
    except UploadFingerprint.DoesNotExist:
        pass

    media_file = MediaFile(
        bucket=settings.MEDIA_STORAGE_BUCKET_NAME,
        file_name=normalize_file_name(data.file_name),
        content_type=data.content_type,
        uploaded_by=request.user,
    )
    media_file.key = build_media_key(
        request.user.pk,
        media_file.id,
        data.file_name,
        data.content_type,
    )

    try:
        with transaction.atomic():
            media_file.save()
            UploadFingerprint.objects.create(
                fingerprint=fingerprint,
                media_file=media_file,
            )
    except IntegrityError:
        return (
            UploadFingerprint.objects.select_related("media_file")
            .get(
                fingerprint=fingerprint,
            )
            .media_file
        )

    return media_file


@router.post("/upload/", response=UploadInitResponseSchema)
def initialize_upload(request, data: UploadInitSchema):
    media_file = _ensure_media_file_for_init(request, data)
    return _build_init_response(media_file)


def _normalize_etag(etag: str | None) -> str | None:
    if etag is None:
        return None
    return etag.strip('"')


@router.post("/upload/confirm/", response=MediaFileSchema)
def confirm_upload(request, data: UploadConfirmSchema):
    with transaction.atomic():
        try:
            media_file = MediaFile.objects.select_for_update().get(
                id=data.id,
                uploaded_by=request.user,
                deleted_at__isnull=True,
            )
        except MediaFile.DoesNotExist as exc:
            raise HttpError(404, "Media file not found") from exc

        if media_file.status == MediaFileStatus.UPLOADED:
            return media_file

        try:
            object_info = head_object(media_file)
        except Exception as exc:
            media_file.status = MediaFileStatus.FAILED
            media_file.save(update_fields=["status", "updated_at"])
            raise HttpError(404, "Uploaded object not found") from exc

        actual_size = int(object_info["ContentLength"])
        actual_etag = _normalize_etag(
            object_info.get("ETag") if isinstance(object_info, dict) else None,
        )
        if data.size is not None and data.size != actual_size:
            raise HttpError(400, "Reported file size does not match stored object")
        if data.etag is not None and _normalize_etag(data.etag) != actual_etag:
            raise HttpError(400, "Reported etag does not match stored object")

        media_file.size = actual_size
        media_file.etag = actual_etag
        media_file.status = MediaFileStatus.UPLOADED
        media_file.save(update_fields=["size", "etag", "status", "updated_at"])
        return media_file


@router.get("/{media_id}/", response=MediaFileSchema)
def retrieve_media(request, media_id: UUID):
    return get_object_or_404(_media_queryset(request), id=media_id)


@router.get("/{media_id}/url/", response=MediaUrlSchema)
def retrieve_media_url(request, media_id: UUID):
    media_file = get_object_or_404(_media_queryset(request), id=media_id)
    if media_file.status != MediaFileStatus.UPLOADED:
        raise HttpError(409, "Media file is not available yet")
    return MediaUrlSchema(url=generate_presigned_get_url(media_file))


@router.delete("/{media_id}/", response=MediaFileSchema)
def delete_media(request, media_id: UUID):
    with transaction.atomic():
        try:
            media_file = MediaFile.objects.select_for_update().get(
                id=media_id,
                uploaded_by=request.user,
                deleted_at__isnull=True,
            )
        except MediaFile.DoesNotExist as exc:
            raise HttpError(404, "Media file not found") from exc

        delete_object(media_file)
        media_file.deleted_at = timezone.now()
        media_file.save(update_fields=["deleted_at", "updated_at"])
        return media_file
