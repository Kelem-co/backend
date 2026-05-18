from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.mcp_backend_docs.server import JSONRPC_VERSION
from core.mcp_backend_docs.server import build_server_from_env


def _jsonrpc_error(
    *,
    code: int,
    message: str,
    status: HTTPStatus,
    message_id: str | int | None = None,
) -> JsonResponse:
    return JsonResponse(
        {
            "jsonrpc": JSONRPC_VERSION,
            "id": message_id,
            "error": {"code": code, "message": message},
        },
        status=status,
    )


@csrf_exempt
@require_POST
def mcp_endpoint(request: HttpRequest) -> HttpResponse:
    try:
        payload: Any = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError, UnicodeDecodeError:
        return _jsonrpc_error(
            code=-32700,
            message="Request body must be valid JSON.",
            status=HTTPStatus.BAD_REQUEST,
        )

    if not isinstance(payload, dict):
        return _jsonrpc_error(
            code=-32600,
            message="Request body must be a single JSON-RPC object.",
            status=HTTPStatus.BAD_REQUEST,
        )

    response = build_server_from_env().handle_message(payload)
    if response is None:
        return HttpResponse(status=HTTPStatus.ACCEPTED)
    return JsonResponse(response)
