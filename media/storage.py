from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


class S3StorageClient:
    def __init__(self) -> None:
        self.settings = settings.MEDIA_UPLOAD_SETTINGS
        self.bucket = self.settings["BUCKET_NAME"]
        self.region = self.settings["REGION"]
        self.endpoint_url = self.settings["ENDPOINT_URL"]
        self.internal_endpoint_url = (
            self.settings["INTERNAL_ENDPOINT_URL"] or self.endpoint_url
        )
        self.access_key = settings.S3_ACCESS_KEY_ID
        self.secret_key = settings.S3_SECRET_ACCESS_KEY

        self.client: S3Client = self._build_client(self.internal_endpoint_url)
        self.presign_client: S3Client = self._build_client(self.endpoint_url)

    def _build_client(self, endpoint_url: str) -> S3Client:
        return boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=boto3.session.Config(s3={"addressing_style": "path"})
            if endpoint_url
            else boto3.session.Config(),
        )

    def create_multipart_upload(
        self,
        key: str,
        content_type: str | None = None,
    ) -> str:
        try:
            params = {
                "Bucket": self.bucket,
                "Key": key,
            }
            if content_type:
                params["ContentType"] = content_type

            response = self.client.create_multipart_upload(
                **params,
            )
            upload_id = response["UploadId"]
            logger.info(
                "Created multipart upload for key=%s, upload_id=%s",
                key,
                upload_id,
            )
        except ClientError:
            logger.exception("Failed to create multipart upload for key=%s", key)
            raise
        else:
            return upload_id

    def get_presigned_part_url(
        self,
        key: str,
        upload_id: str,
        part_number: int,
        expires_in: int,
    ) -> str:
        try:
            url = self.presign_client.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expires_in,
            )
            logger.info(
                "Generated presigned multipart URL for key=%s, upload_id=%s, part=%s, expires_in=%ss",  # noqa: E501
                key,
                upload_id,
                part_number,
                expires_in,
            )
        except ClientError:
            logger.exception(
                "Failed to generate multipart part URL for key=%s, upload_id=%s, part=%s",  # noqa: E501
                key,
                upload_id,
                part_number,
            )
            raise
        else:
            return url

    def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        parts: list[dict[str, str | int]],
    ) -> dict[str, Any]:
        try:
            response = self.client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            logger.info(
                "Completed multipart upload for key=%s, upload_id=%s",
                key,
                upload_id,
            )
        except ClientError:
            logger.exception(
                "Failed to complete multipart upload for key=%s, upload_id=%s",
                key,
                upload_id,
            )
            raise
        else:
            return response

    def abort_multipart_upload(self, key: str, upload_id: str) -> bool:
        try:
            self.client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
            )
            logger.info(
                "Aborted multipart upload for key=%s, upload_id=%s",
                key,
                upload_id,
            )
        except ClientError:
            logger.exception(
                "Failed to abort multipart upload for key=%s, upload_id=%s",
                key,
                upload_id,
            )
            raise
        else:
            return True

    def get_download_url(
        self,
        key: str,
        expires_in: int | None = None,
    ) -> str:
        if expires_in is None:
            expires_in = self.settings["DOWNLOAD_URL_TTL"]

        try:
            url = self.presign_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            logger.info(
                "Generated presigned GET URL for key=%s, expires_in=%ss",
                key,
                expires_in,
            )
        except ClientError:
            logger.exception("Failed to generate download URL for key=%s", key)
            raise
        else:
            return url

    def head_object(self, key: str) -> dict[str, Any]:
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
            return {
                "exists": True,
                "etag": response.get("ETag", "").strip('"'),
                "size": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info("Object not found: key=%s", key)
                return {
                    "exists": False,
                    "etag": None,
                    "size": None,
                    "content_type": None,
                }
            logger.exception("Error checking object: key=%s", key)
            raise

    def delete_object(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info("Deleted object: key=%s", key)
        except ClientError:
            logger.exception("Failed to delete object: key=%s", key)
            raise
        else:
            return True

    def delete_objects(self, keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {"deleted": [], "errors": []}

        try:
            delete_list = [{"Key": key} for key in keys]
            response = self.client.delete_objects(
                Bucket=self.bucket,
                Delete={"Objects": delete_list},
            )
            deleted = [obj["Key"] for obj in response.get("Deleted", [])]
            errors = response.get("Errors", [])
            logger.info(
                "Batch delete: deleted=%s, errors=%s",
                len(deleted),
                len(errors),
            )
        except ClientError:
            logger.exception("Failed batch delete")
            raise
        else:
            return {"deleted": deleted, "errors": errors}
