from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import BinaryIO

from core.mcp_backend_docs.openapi import OpenAPISchemaLoader
from core.mcp_backend_docs.openapi import SchemaLoadError
from core.mcp_backend_docs.openapi import SchemaSourceConfig
from core.mcp_backend_docs.openapi import render_resource_text

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"
RESOURCE_URI_PREFIX = "resource://backend-api-docs/"


@dataclass(slots=True, frozen=True)
class ResourceDefinition:
    name: str
    uri: str
    description: str
    mime_type: str = "application/json"


RESOURCE_DEFINITIONS = (
    ResourceDefinition(
        name="openapi-schema",
        uri=f"{RESOURCE_URI_PREFIX}openapi-schema",
        description="Raw OpenAPI schema fetched from the backend schema endpoint.",
    ),
    ResourceDefinition(
        name="api-summary",
        uri=f"{RESOURCE_URI_PREFIX}api-summary",
        description="Normalized API operation summary derived from the OpenAPI schema.",
    ),
)


class StdioMessageIO:
    def __init__(self, input_stream: BinaryIO, output_stream: BinaryIO) -> None:
        self.input_stream = input_stream
        self.output_stream = output_stream

    def read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            raw_line = self.input_stream.readline()
            if raw_line == b"":
                return None
            line = raw_line.decode("utf-8").strip()
            if not line:
                break
            key, _, value = line.partition(":")
            headers[key.lower()] = value.strip()

        content_length = int(headers["content-length"])
        payload = self.input_stream.read(content_length)
        return json.loads(payload.decode("utf-8"))

    def write_message(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(encoded)}\r\n\r\n".encode()
        self.output_stream.write(header)
        self.output_stream.write(encoded)
        self.output_stream.flush()


class BackendAPIDocsMCPServer:
    def __init__(self, loader: OpenAPISchemaLoader) -> None:
        self.loader = loader
        self.resource_map = {
            resource.uri: resource for resource in RESOURCE_DEFINITIONS
        }
        self.resource_map.update(
            {resource.name: resource for resource in RESOURCE_DEFINITIONS},
        )

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params", {})

        if message_id is None:
            return None

        try:
            result = self._dispatch(message_id, method, params)
        except SchemaLoadError as exc:
            return self._error(message_id, -32001, str(exc))
        return result

    def _dispatch(
        self,
        message_id: str | int,
        method: Any,
        params: Any,
    ) -> dict[str, Any]:
        if method in {"ping", "tools/list"}:
            result_map = {
                "ping": {},
                "tools/list": {"tools": []},
            }
            return self._success(message_id, result_map[method])
        if method == "resources/read":
            uri = params.get("uri") if isinstance(params, dict) else None
            if not isinstance(uri, str):
                return self._error(
                    message_id,
                    -32602,
                    "resources/read requires a string 'uri' parameter.",
                )
            return self._read_resource(message_id, uri)

        handler_map = {
            "initialize": self._initialize,
            "resources/list": self._list_resources,
        }
        handler = handler_map.get(method)
        if handler is not None:
            return handler(message_id)
        return self._error(message_id, -32601, f"Method not found: {method}.")

    def _initialize(self, message_id: str | int) -> dict[str, Any]:
        return self._success(
            message_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"resources": {}},
                "serverInfo": {
                    "name": "backend-api-docs-mcp",
                    "version": "0.1.0",
                },
            },
        )

    def _list_resources(self, message_id: str | int) -> dict[str, Any]:
        return self._success(
            message_id,
            {
                "resources": [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mime_type,
                    }
                    for resource in RESOURCE_DEFINITIONS
                ],
            },
        )

    def _read_resource(self, message_id: str | int, uri: str) -> dict[str, Any]:
        resource = self.resource_map.get(uri)
        if resource is None:
            return self._error(message_id, -32602, f"Unknown resource URI: {uri}.")

        schema = self.loader.load()
        text = render_resource_text(resource.name, schema)
        return self._success(
            message_id,
            {
                "contents": [
                    {
                        "uri": resource.uri,
                        "mimeType": resource.mime_type,
                        "text": text,
                    },
                ],
            },
        )

    def _success(self, message_id: str | int, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": JSONRPC_VERSION, "id": message_id, "result": result}

    def _error(
        self,
        message_id: str | int,
        code: int,
        message: str,
    ) -> dict[str, Any]:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": message_id,
            "error": {"code": code, "message": message},
        }


def load_config_from_env() -> SchemaSourceConfig:
    fallback_value = os.getenv("BACKEND_API_SCHEMA_FALLBACK_PATH")
    auth_token = os.getenv("BACKEND_API_SCHEMA_AUTH_TOKEN")
    return SchemaSourceConfig(
        schema_url=os.getenv(
            "BACKEND_API_SCHEMA_URL",
            "http://127.0.0.1:8000/api/schema/",
        ),
        fallback_path=Path(fallback_value) if fallback_value else None,
        timeout_seconds=float(os.getenv("BACKEND_API_SCHEMA_TIMEOUT_SECONDS", "5")),
        auth_header=os.getenv("BACKEND_API_SCHEMA_AUTH_HEADER", "Authorization"),
        auth_scheme=os.getenv("BACKEND_API_SCHEMA_AUTH_SCHEME", "Bearer"),
        auth_token=auth_token or None,
    )


def build_server_from_env() -> BackendAPIDocsMCPServer:
    return BackendAPIDocsMCPServer(OpenAPISchemaLoader(load_config_from_env()))


def main() -> None:
    server = build_server_from_env()
    message_io = StdioMessageIO(sys.stdin.buffer, sys.stdout.buffer)

    while True:
        message = message_io.read_message()
        if message is None:
            return
        response = server.handle_message(message)
        if response is not None:
            message_io.write_message(response)
