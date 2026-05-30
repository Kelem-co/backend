from __future__ import annotations

import json
from base64 import b64encode
from http import HTTPStatus
from urllib import error
from urllib import parse
from urllib import request
from urllib.parse import urlsplit

from django.conf import settings

from .sms import BaseSMSBackend


class SMSDeliveryError(RuntimeError):
    """Raised when an SMS provider fails to accept or deliver a message."""


class TelerivetSMSBackend(BaseSMSBackend):
    API_BASE_URL = "https://api.telerivet.com/v1"

    @staticmethod
    def _raise_delivery_error(message: str) -> None:
        raise SMSDeliveryError(message)

    @staticmethod
    def _validate_https_url(url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc:
            message = "Telerivet endpoint must be a valid HTTPS URL."
            TelerivetSMSBackend._raise_delivery_error(message)

    def send_message(self, *, to: str, body: str) -> None:
        api_key = settings.TELERIVET_API_KEY
        project_id = settings.TELERIVET_PROJECT_ID
        timeout_seconds = settings.TELERIVET_TIMEOUT_SECONDS

        endpoint = f"{self.API_BASE_URL}/projects/{project_id}/messages/send"
        self._validate_https_url(endpoint)
        payload = parse.urlencode({"to_number": to, "content": body}).encode("utf-8")
        encoded_credentials = b64encode(f"{api_key}:".encode()).decode("ascii")
        req = request.Request(  # noqa: S310
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:  # noqa: S310
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            message = f"Telerivet SMS request failed with status {exc.code}: {detail}"
            raise SMSDeliveryError(message) from exc
        except error.URLError as exc:
            message = f"Telerivet SMS request failed: {exc.reason}"
            raise SMSDeliveryError(message) from exc

        if status_code >= HTTPStatus.BAD_REQUEST:
            message = (
                f"Telerivet SMS request failed with status {status_code}: {raw_body}"
            )
            self._raise_delivery_error(message)

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            message = "Telerivet SMS response was not valid JSON."
            raise SMSDeliveryError(message) from exc

        if isinstance(parsed, dict) and parsed.get("status") == "error":
            provider_message = parsed.get("message", "Unknown error")
            message = f"Telerivet SMS provider error: {provider_message}"
            self._raise_delivery_error(message)
