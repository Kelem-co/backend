from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from urllib import error
from urllib import parse
from urllib import request

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised by runtime env
    yaml = None

if TYPE_CHECKING:
    from pathlib import Path


class SchemaLoadError(RuntimeError):
    """Raised when the OpenAPI schema cannot be loaded."""


@dataclass(slots=True, frozen=True)
class SchemaSourceConfig:
    schema_url: str = "http://127.0.0.1:8000/api/schema/"
    fallback_path: Path | None = None
    timeout_seconds: float = 5.0
    auth_header: str = "Authorization"
    auth_scheme: str = "Bearer"
    auth_token: str | None = None


def _with_json_format(schema_url: str) -> str:
    parsed = parse.urlsplit(schema_url)
    query = parse.parse_qs(parsed.query, keep_blank_values=True)
    query.setdefault("format", ["json"])
    encoded_query = parse.urlencode(query, doseq=True)
    return parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, encoded_query, parsed.fragment),
    )


def _json_dumps(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _optional_yaml_load(raw_text: str) -> dict[str, Any]:
    if yaml is None:
        msg = "Schema content was not valid JSON and PyYAML is not installed."
        raise SchemaLoadError(msg)

    loaded = yaml.safe_load(raw_text)
    if not isinstance(loaded, dict):
        msg = "Schema payload must deserialize to a JSON object."
        raise SchemaLoadError(msg)
    return loaded


def parse_schema_payload(raw_text: str) -> dict[str, Any]:
    try:
        loaded = json.loads(raw_text)
    except json.JSONDecodeError:
        return _optional_yaml_load(raw_text)

    if not isinstance(loaded, dict):
        msg = "Schema payload must deserialize to a JSON object."
        raise SchemaLoadError(msg)
    return loaded


class OpenAPISchemaLoader:
    def __init__(self, config: SchemaSourceConfig) -> None:
        self.config = config

    def load(self) -> dict[str, Any]:
        try:
            return self._load_live_schema()
        except SchemaLoadError as live_error:
            if self.config.fallback_path is None:
                raise
            try:
                return self._load_fallback_schema()
            except SchemaLoadError as fallback_error:
                msg = (
                    "Unable to load OpenAPI schema from the live backend "
                    "or fallback file. "
                    f"Live error: {live_error}. Fallback error: {fallback_error}."
                )
                raise SchemaLoadError(msg) from fallback_error

    def _build_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.auth_token:
            headers[self.config.auth_header] = (
                f"{self.config.auth_scheme} {self.config.auth_token}".strip()
            )
        return headers

    def _load_live_schema(self) -> dict[str, Any]:
        schema_url = _with_json_format(self.config.schema_url)
        parsed_url = parse.urlsplit(schema_url)
        if parsed_url.scheme not in {"http", "https"}:
            msg = f"Unsupported schema URL scheme: {parsed_url.scheme}."
            raise SchemaLoadError(msg)
        schema_request = request.Request(  # noqa: S310
            schema_url,
            headers=self._build_headers(),
        )
        try:
            with request.urlopen(  # noqa: S310
                schema_request,
                timeout=self.config.timeout_seconds,
            ) as response:
                payload = response.read().decode("utf-8")
        except error.HTTPError as exc:
            msg = f"Live schema fetch failed with HTTP {exc.code} for {schema_url}."
            raise SchemaLoadError(msg) from exc
        except error.URLError as exc:
            msg = f"Live schema fetch failed for {schema_url}: {exc.reason}."
            raise SchemaLoadError(msg) from exc
        return parse_schema_payload(payload)

    def _load_fallback_schema(self) -> dict[str, Any]:
        assert self.config.fallback_path is not None
        try:
            payload = self.config.fallback_path.read_text(encoding="utf-8")
        except OSError as exc:
            msg = (
                f"Fallback schema file could not be read: {self.config.fallback_path}."
            )
            raise SchemaLoadError(msg) from exc
        return parse_schema_payload(payload)


def _auth_required(
    operation: dict[str, Any],
    global_security: list[dict[str, list[str]]] | None,
) -> bool:
    operation_security = operation.get("security", global_security)
    return bool(operation_security)


HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "options", "head", "trace"},
)


def summarize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        msg = "OpenAPI schema is missing a valid 'paths' object."
        raise SchemaLoadError(msg)

    global_security = schema.get("security")
    operations: list[dict[str, Any]] = []
    for path, path_item in sorted(paths.items()):
        if not isinstance(path_item, dict):
            continue
        for method, operation in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            summary = str(operation.get("summary") or "").strip()
            description = str(operation.get("description") or "").strip()
            operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "title": summary or str(operation.get("operationId") or ""),
                    "description": description,
                    "tags": [
                        str(tag)
                        for tag in operation.get("tags", [])
                        if isinstance(tag, str)
                    ],
                    "auth_required": _auth_required(operation, global_security),
                },
            )

    info = schema.get("info", {})
    return {
        "title": info.get("title"),
        "version": info.get("version"),
        "description": info.get("description"),
        "operations": operations,
    }


def render_resource_text(resource_name: str, schema: dict[str, Any]) -> str:
    if resource_name == "openapi-schema":
        return _json_dumps(schema)
    if resource_name == "api-summary":
        return _json_dumps(summarize_schema(schema))
    msg = f"Unknown resource: {resource_name}."
    raise SchemaLoadError(msg)
