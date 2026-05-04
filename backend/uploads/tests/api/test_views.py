from __future__ import annotations

from http import HTTPStatus

import pytest
from django.urls import reverse

from backend.uploads.models import MediaFile
from backend.uploads.models import MediaFileStatus
from backend.uploads.models import UploadFingerprint
from backend.uploads.tests.factories import MediaFileFactory

pytestmark = pytest.mark.django_db


class FakeS3Client:
    def __init__(self):
        self.head_calls = []
        self.deleted = []

    def generate_presigned_post(self, **kwargs):
        return {
            "url": "https://example.test/upload",
            "fields": {
                "key": kwargs["Key"],
                "Content-Type": kwargs["Fields"]["Content-Type"],
            },
        }

    def generate_presigned_url(self, operation_name, Params, ExpiresIn):
        return f"https://example.test/get/{Params['Key']}"

    def head_object(self, Bucket, Key):
        self.head_calls.append((Bucket, Key))
        return {"ContentLength": 12345, "ETag": '"abc123"'}

    def delete_object(self, Bucket, Key):
        self.deleted.append((Bucket, Key))


@pytest.fixture
def fake_s3(monkeypatch):
    client = FakeS3Client()
    monkeypatch.setattr("backend.uploads.services.get_s3_client", lambda: client)
    return client


def test_initialize_upload_is_idempotent(client, user, fake_s3):
    client.force_login(user)

    payload = {"file_name": "image.png", "content_type": "image/png"}
    url = reverse("api:initialize_upload")

    response = client.post(url, data=payload, content_type="application/json")
    assert response.status_code == HTTPStatus.OK, response.json()
    first = response.json()

    response = client.post(url, data=payload, content_type="application/json")
    assert response.status_code == HTTPStatus.OK, response.json()
    second = response.json()

    assert first["id"] == second["id"]
    assert first["key"] == second["key"]
    assert first["upload_url"] == "https://example.test/upload"
    assert first["fields"]["Content-Type"] == "image/png"
    assert MediaFile.objects.count() == 1
    assert UploadFingerprint.objects.count() == 1


def test_confirm_upload_is_idempotent(client, user, fake_s3):
    client.force_login(user)
    media = MediaFileFactory.create(uploaded_by=user, status=MediaFileStatus.PENDING)

    response = client.post(
        reverse("api:confirm_upload"),
        data={"id": str(media.id), "size": 12345, "etag": "abc123"},
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["status"] == MediaFileStatus.UPLOADED

    response = client.post(
        reverse("api:confirm_upload"),
        data={"id": str(media.id), "size": 12345, "etag": "abc123"},
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["status"] == MediaFileStatus.UPLOADED
