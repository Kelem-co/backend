from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch
from urllib import error

import pytest
from accounts.sms import get_sms_backend
from accounts.sms_backends import SMSDeliveryError
from accounts.sms_backends import TelerivetSMSBackend
from django.test import override_settings


@override_settings(
    TELERIVET_API_KEY="test-api-key",
    TELERIVET_PROJECT_ID="PJ123456",
    TELERIVET_TIMEOUT_SECONDS=5,
)
def test_telerivet_sms_backend_sends_message_successfully() -> None:
    backend = TelerivetSMSBackend()
    mocked_response = Mock()
    mocked_response.getcode.return_value = 200
    mocked_response.read.return_value = b'{"status":"queued","id":"msg_123"}'
    mocked_response.__enter__ = Mock(return_value=mocked_response)
    mocked_response.__exit__ = Mock(return_value=False)

    with patch("accounts.sms_backends.request.urlopen", return_value=mocked_response):
        backend.send_message(to="+251911111111", body="Hello from test")


@override_settings(
    TELERIVET_API_KEY="test-api-key",
    TELERIVET_PROJECT_ID="PJ123456",
    TELERIVET_TIMEOUT_SECONDS=5,
)
def test_telerivet_sms_backend_raises_on_provider_error_response() -> None:
    backend = TelerivetSMSBackend()
    mocked_response = Mock()
    mocked_response.getcode.return_value = 200
    mocked_response.read.return_value = (
        b'{"status":"error","message":"invalid recipient"}'
    )
    mocked_response.__enter__ = Mock(return_value=mocked_response)
    mocked_response.__exit__ = Mock(return_value=False)

    with (
        patch("accounts.sms_backends.request.urlopen", return_value=mocked_response),
        pytest.raises(SMSDeliveryError, match="provider error"),
    ):
        backend.send_message(to="+251911111111", body="Hello from test")


@override_settings(
    TELERIVET_API_KEY="test-api-key",
    TELERIVET_PROJECT_ID="PJ123456",
    TELERIVET_TIMEOUT_SECONDS=5,
)
def test_telerivet_sms_backend_raises_on_network_error() -> None:
    backend = TelerivetSMSBackend()

    with (
        patch(
            "accounts.sms_backends.request.urlopen",
            side_effect=error.URLError("connection refused"),
        ),
        pytest.raises(SMSDeliveryError, match="connection refused"),
    ):
        backend.send_message(to="+251911111111", body="Hello from test")


@override_settings(SMS_BACKEND="accounts.sms_backends.TelerivetSMSBackend")
def test_sms_backend_setting_resolves_telerivet_backend() -> None:
    backend = get_sms_backend()
    assert isinstance(backend, TelerivetSMSBackend)
