from __future__ import annotations

import json
from copy import deepcopy
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Self
from urllib import error
from urllib import request

import pytest
from django.conf import settings
from django.test import Client
from django.test import override_settings
from django.urls import reverse

from core.mcp_backend_docs.openapi import OpenAPISchemaLoader
from core.mcp_backend_docs.openapi import SchemaLoadError
from core.mcp_backend_docs.openapi import SchemaSourceConfig
from core.mcp_backend_docs.openapi import summarize_schema
from core.mcp_backend_docs.server import RESOURCE_DEFINITIONS
from core.mcp_backend_docs.server import BackendAPIDocsMCPServer

if TYPE_CHECKING:
    from pathlib import Path


SCHEMA_TIMEOUT_SECONDS = 5.0
_NO_THROTTLE_SETTINGS = deepcopy(settings.REST_FRAMEWORK)
_NO_THROTTLE_SETTINGS["DEFAULT_THROTTLE_CLASSES"] = []
_NO_THROTTLE_SETTINGS["DEFAULT_THROTTLE_RATES"] = {}


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload.encode("utf-8")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _post_mcp_message(client: Client, payload: dict[str, object]) -> object:
    return client.post(
        reverse("backend-api-docs-mcp"),
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=_NO_THROTTLE_SETTINGS)
def test_openapi_resource_exposes_live_schema_from_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_response = Client().get(f"{reverse('api-schema')}?format=json")
    assert schema_response.status_code == HTTPStatus.OK
    schema_text = schema_response.content.decode("utf-8")

    def fake_urlopen(req: request.Request, timeout: float) -> _FakeResponse:
        assert req.full_url.endswith("/api/schema/?format=json")
        assert req.headers["Accept"] == "application/json"
        assert timeout == SCHEMA_TIMEOUT_SECONDS
        return _FakeResponse(schema_text)

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    server = BackendAPIDocsMCPServer(
        OpenAPISchemaLoader(SchemaSourceConfig()),
    )
    response = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": RESOURCE_DEFINITIONS[0].uri},
        },
    )

    assert response is not None
    contents = response["result"]["contents"][0]
    schema = json.loads(contents["text"])
    assert "/api/users/" in schema["paths"]
    assert "/api/organizations/" in schema["paths"]


@pytest.mark.django_db
def test_network_mcp_endpoint_supports_initialize() -> None:
    response = _post_mcp_message(
        Client(),
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["result"]["protocolVersion"] == "2024-11-05"
    assert payload["result"]["serverInfo"]["name"] == "backend-api-docs-mcp"


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=_NO_THROTTLE_SETTINGS)
def test_network_mcp_endpoint_reads_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_response = Client().get(f"{reverse('api-schema')}?format=json")
    assert schema_response.status_code == HTTPStatus.OK
    schema_text = schema_response.content.decode("utf-8")

    def fake_urlopen(req: request.Request, timeout: float) -> _FakeResponse:
        assert req.full_url.endswith("/api/schema/?format=json")
        assert req.headers["Accept"] == "application/json"
        assert timeout == SCHEMA_TIMEOUT_SECONDS
        return _FakeResponse(schema_text)

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    response = _post_mcp_message(
        Client(),
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/read",
            "params": {"uri": RESOURCE_DEFINITIONS[1].uri},
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    contents = payload["result"]["contents"][0]
    summary = json.loads(contents["text"])
    assert any(item["path"] == "/api/users/me/" for item in summary["operations"])


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=_NO_THROTTLE_SETTINGS)
def test_api_summary_contains_expected_fields_from_schema() -> None:
    schema_response = Client().get(f"{reverse('api-schema')}?format=json")
    assert schema_response.status_code == HTTPStatus.OK

    summary = summarize_schema(json.loads(schema_response.content))
    operations = {
        (item["method"], item["path"]): item for item in summary["operations"]
    }

    me_operation = operations[("GET", "/api/users/me/")]
    assert me_operation["title"] == "users_me_retrieve"
    assert me_operation["description"] == ""
    assert me_operation["auth_required"] is True
    assert me_operation["tags"] == ["users"]


def test_api_summary_preserves_summary_and_description_when_present() -> None:
    summary = summarize_schema(
        {
            "openapi": "3.0.3",
            "info": {"title": "Example API", "version": "1.0.0"},
            "paths": {
                "/api/example/": {
                    "get": {
                        "summary": "Example list",
                        "description": "List example objects for agents.",
                        "tags": ["examples"],
                        "security": [],
                    },
                },
            },
            "security": [{"jwtAuth": []}],
        },
    )

    operation = summary["operations"][0]
    assert operation["method"] == "GET"
    assert operation["path"] == "/api/example/"
    assert operation["title"] == "Example list"
    assert operation["description"] == "List example objects for agents."
    assert operation["auth_required"] is False
    assert operation["tags"] == ["examples"]


def test_loader_uses_fallback_file_when_backend_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fallback_path = tmp_path / "schema.json"
    fallback_path.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Fallback API", "version": "1.0.0"},
                "paths": {"/api/health/": {"get": {"summary": "Health check"}}},
            },
        ),
        encoding="utf-8",
    )

    def fake_urlopen(req: request.Request, timeout: float) -> _FakeResponse:
        msg = "connection refused"
        raise error.URLError(msg)

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    loader = OpenAPISchemaLoader(
        SchemaSourceConfig(fallback_path=fallback_path),
    )
    schema = loader.load()

    assert schema["info"]["title"] == "Fallback API"
    assert "/api/health/" in schema["paths"]


def test_loader_raises_clear_error_when_backend_and_fallback_fail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.json"

    def fake_urlopen(req: request.Request, timeout: float) -> _FakeResponse:
        raise error.HTTPError(
            req.full_url,
            403,
            "forbidden",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    loader = OpenAPISchemaLoader(
        SchemaSourceConfig(
            fallback_path=missing_path,
            auth_token="test-token",  # noqa: S106
        ),
    )

    with pytest.raises(SchemaLoadError) as exc_info:
        loader.load()

    message = str(exc_info.value)
    assert "live backend or fallback file" in message
    assert "HTTP 403" in message
    assert str(missing_path) in message


def test_loader_sends_auth_header_when_token_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_headers: dict[str, str] = {}

    def fake_urlopen(req: request.Request, timeout: float) -> _FakeResponse:
        captured_headers.update(req.headers)
        return _FakeResponse(
            json.dumps(
                {
                    "openapi": "3.0.3",
                    "info": {"title": "Auth API", "version": "1.0.0"},
                    "paths": {},
                },
            ),
        )

    monkeypatch.setattr(request, "urlopen", fake_urlopen)

    loader = OpenAPISchemaLoader(
        SchemaSourceConfig(
            auth_token="test-token",  # noqa: S106
            auth_scheme="Token",
        ),
    )
    loader.load()

    assert captured_headers["Authorization"] == "Token test-token"
