from __future__ import annotations

import hashlib
import mimetypes
import uuid
from functools import lru_cache
from pathlib import PurePath

import boto3
from botocore.config import Config
from django.conf import settings
from django.utils import timezone

from backend.uploads.models import MediaFile

ALLOWED_CONTENT_TYPES = set(settings.MEDIA_STORAGE_ALLOWED_CONTENT_TYPES)


def validate_content_type(content_type: str) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported content type: {content_type}")


def normalize_file_name(file_name: str) -> str:
    return PurePath(file_name).name


def _extension_for_file_name(file_name: str, content_type: str) -> str:
    suffix = PurePath(file_name).suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(content_type)
    if guessed:
        return guessed
    raise ValueError("Could not determine file extension")


def build_media_key(
    user_id: int,
    media_id: uuid.UUID,
    file_name: str,
    content_type: str,
) -> str:
    extension = _extension_for_file_name(file_name, content_type)
    return f"uploads/{user_id}/{media_id}{extension}"


def build_upload_fingerprint(user_id: int, file_name: str, content_type: str) -> str:
    window_seconds = settings.MEDIA_STORAGE_FINGERPRINT_WINDOW_SECONDS
    window = int(timezone.now().timestamp()) // window_seconds
    material = f"{user_id}:{normalize_file_name(file_name)}:{content_type}:{window}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MEDIA_STORAGE_ENDPOINT_URL,
        aws_access_key_id=settings.MEDIA_STORAGE_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.MEDIA_STORAGE_SECRET_ACCESS_KEY or None,
        region_name=settings.MEDIA_STORAGE_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_post(media_file: MediaFile) -> dict[str, object]:
    return get_s3_client().generate_presigned_post(
        Bucket=media_file.bucket,
        Key=media_file.key,
        Fields={"Content-Type": media_file.content_type},
        Conditions=[
            {"Content-Type": media_file.content_type},
            ["content-length-range", 1, settings.MEDIA_STORAGE_MAX_UPLOAD_SIZE],
        ],
        ExpiresIn=settings.MEDIA_STORAGE_PRESIGNED_URL_EXPIRATION,
    )


def generate_presigned_get_url(media_file: MediaFile) -> str:
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": media_file.bucket, "Key": media_file.key},
        ExpiresIn=settings.MEDIA_STORAGE_PRESIGNED_URL_EXPIRATION,
    )


def head_object(media_file: MediaFile) -> dict[str, object]:
    return get_s3_client().head_object(Bucket=media_file.bucket, Key=media_file.key)


def delete_object(media_file: MediaFile) -> None:
    get_s3_client().delete_object(Bucket=media_file.bucket, Key=media_file.key)
