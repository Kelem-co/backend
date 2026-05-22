from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus

from rest_framework.response import Response
from rest_framework.views import exception_handler


def _default_error_code(status_code: int) -> str:
    if status_code == HTTPStatus.BAD_REQUEST:
        return "bad_request"
    if status_code == HTTPStatus.UNAUTHORIZED:
        return "not_authenticated"
    if status_code == HTTPStatus.FORBIDDEN:
        return "permission_denied"
    if status_code == HTTPStatus.NOT_FOUND:
        return "not_found"
    return "error"


def _normalize_errors(
    data: object,
    *,
    status_code: int,
    field: str | None = None,
) -> list[dict[str, str | None]]:
    if isinstance(data, list):
        return [
            {
                "code": getattr(item, "code", _default_error_code(status_code)),
                "detail": str(item),
                "field": field,
            }
            for item in data
        ]

    if isinstance(data, Mapping):
        if "detail" in data and len(data) == 1:
            detail = data["detail"]
            return [
                {
                    "code": getattr(detail, "code", _default_error_code(status_code)),
                    "detail": str(detail),
                    "field": field,
                },
            ]

        errors: list[dict[str, str | None]] = []
        for key, value in data.items():
            next_field = None if key == "non_field_errors" else str(key)
            errors.extend(
                _normalize_errors(
                    value,
                    status_code=status_code,
                    field=next_field,
                ),
            )
        return errors

    return [
        {
            "code": _default_error_code(status_code),
            "detail": str(data),
            "field": field,
        },
    ]


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    response.data = {
        "errors": _normalize_errors(
            response.data,
            status_code=response.status_code,
        ),
    }
    return response


def error_response(
    *,
    detail: str,
    code: str,
    status_code: int,
    field: str | None = None,
) -> Response:
    return Response(
        {
            "errors": [
                {
                    "code": code,
                    "detail": detail,
                    "field": field,
                },
            ],
        },
        status=status_code,
    )
