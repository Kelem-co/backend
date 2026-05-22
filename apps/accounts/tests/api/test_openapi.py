from http import HTTPStatus

import pytest
import yaml
from django.urls import reverse


def test_api_docs_accessible_by_admin(admin_client):
    url = reverse("api-docs")
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_api_docs_accessible_by_anonymous_users(client):
    url = reverse("api-docs")
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_api_schema_generated_successfully(admin_client):
    url = reverse("api-schema")
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_media_schema_includes_upload_and_download_contracts(admin_client):
    url = reverse("api-schema")
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK

    schema = yaml.safe_load(response.content)
    upload_operation = schema["paths"]["/api/media/upload"]["post"]
    part_url_operation = schema["paths"]["/api/media/{id}/multipart/part-url"]["post"]
    complete_operation = schema["paths"]["/api/media/{id}/multipart/complete"]["post"]
    abort_operation = schema["paths"]["/api/media/{id}/multipart/abort"]["post"]
    retrieve_operation = schema["paths"]["/api/media/{id}"]["get"]
    download_operation = schema["paths"]["/api/media/{id}/url"]["get"]

    request_schema_ref = upload_operation["requestBody"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    created_schema_ref = upload_operation["responses"]["201"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    part_url_request_ref = part_url_operation["requestBody"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    part_url_response_ref = part_url_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    complete_request_ref = complete_operation["requestBody"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    complete_response_ref = complete_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    abort_request_ref = abort_operation["requestBody"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    retrieve_schema_ref = retrieve_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    download_schema_ref = download_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]

    assert request_schema_ref.endswith("/UploadInit")
    assert created_schema_ref.endswith("/UploadResponseEnvelope")
    assert part_url_request_ref.endswith("/MultipartPartUrlRequest")
    assert part_url_response_ref.endswith("/MultipartPartUrlResponseEnvelope")
    assert complete_request_ref.endswith("/MultipartCompleteRequest")
    assert complete_response_ref.endswith("/MultipartStatusResponseEnvelope")
    assert abort_request_ref.endswith("/MultipartAbortRequest")
    assert retrieve_schema_ref.endswith("/MediaFileResponseEnvelope")
    assert download_schema_ref.endswith("/DownloadUrlResponseEnvelope")
    assert "/api/media/{id}/confirm" not in schema["paths"]


def test_user_schema_uses_plain_request_and_plain_response(admin_client):
    url = reverse("api-schema")
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK

    schema = yaml.safe_load(response.content)
    update_operation = schema["paths"]["/api/users/{id}/"]["patch"]
    retrieve_operation = schema["paths"]["/api/users/{id}/"]["get"]

    request_schema_ref = update_operation["requestBody"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    update_schema_ref = update_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    retrieve_schema_ref = retrieve_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]

    assert request_schema_ref.endswith("/PatchedUserUpdate")
    assert update_schema_ref.endswith("/User")
    assert retrieve_schema_ref.endswith("/User")
