from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus


class ApiEnvelopeMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if (
            not hasattr(response, "data")
            or response.status_code >= HTTPStatus.BAD_REQUEST
        ):
            return response

        if self._is_enveloped_payload(response.data):
            return response

        response.data = {"data": response.data}
        return response

    def _is_enveloped_payload(self, data: object) -> bool:
        return (
            isinstance(data, Mapping)
            and "data" in data
            and set(data).issubset(
                {"data", "message"},
            )
        )
