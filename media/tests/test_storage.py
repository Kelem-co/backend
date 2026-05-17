from __future__ import annotations

from unittest import mock

from media.storage import S3StorageClient


@mock.patch("media.storage.boto3.client")
def test_storage_uses_internal_endpoint_for_server_calls(mock_boto_client, settings):
    settings.MEDIA_UPLOAD_SETTINGS["BUCKET_NAME"] = "core-local"
    settings.MEDIA_UPLOAD_SETTINGS["REGION"] = "us-west-2"
    settings.MEDIA_UPLOAD_SETTINGS["ENDPOINT_URL"] = "http://localhost:9023"
    settings.MEDIA_UPLOAD_SETTINGS["INTERNAL_ENDPOINT_URL"] = "http://minio:9000"
    settings.S3_ACCESS_KEY_ID = "minioadmin"
    settings.S3_SECRET_ACCESS_KEY = "password"  # noqa: S105

    internal_client = mock.Mock()
    presign_client = mock.Mock()
    internal_client.create_multipart_upload.return_value = {"UploadId": "upload-123"}
    mock_boto_client.side_effect = [internal_client, presign_client]

    client = S3StorageClient()
    client.head_object("media/test.pdf")
    client.create_multipart_upload("media/test.pdf", content_type="application/pdf")
    client.get_presigned_part_url(
        "media/test.pdf",
        upload_id="upload-123",
        part_number=1,
        expires_in=900,
    )

    assert (
        mock_boto_client.call_args_list[0].kwargs["endpoint_url"] == "http://minio:9000"
    )
    assert (
        mock_boto_client.call_args_list[1].kwargs["endpoint_url"]
        == "http://localhost:9023"
    )
    internal_client.head_object.assert_called_once_with(
        Bucket="core-local",
        Key="media/test.pdf",
    )
    internal_client.create_multipart_upload.assert_called_once_with(
        Bucket="core-local",
        Key="media/test.pdf",
        ContentType="application/pdf",
    )
    presign_client.generate_presigned_url.assert_called_once()
