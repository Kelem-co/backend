from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SMSMessage:
    to: str
    body: str


sent_sms_messages: list[SMSMessage] = []


class BaseSMSBackend:
    def send_message(self, *, to: str, body: str) -> None:
        raise NotImplementedError


class LoggingSMSBackend(BaseSMSBackend):
    def send_message(self, *, to: str, body: str) -> None:
        sent_sms_messages.append(SMSMessage(to=to, body=body))
        logger.info("SMS to %s: %s", to, body)


def get_sms_backend() -> BaseSMSBackend:
    backend_path = getattr(
        settings,
        "SMS_BACKEND",
        "accounts.sms.LoggingSMSBackend",
    )
    backend_class = import_string(backend_path)
    return backend_class()


def send_sms_message(*, to: str, body: str) -> None:
    get_sms_backend().send_message(to=to, body=body)


def send_parent_invitation_sms(*, phone_number: str, invitation_url: str) -> None:
    send_sms_message(
        to=phone_number,
        body=(
            "You have been invited to access the parent portal. "
            f"Open this link to activate your account: {invitation_url}"
        ),
    )


def send_parent_otp_sms(*, phone_number: str, otp_code: str) -> None:
    send_sms_message(
        to=phone_number,
        body=(
            "Your parent login code is "
            f"{otp_code}. It expires in "
            f"{settings.PARENT_OTP_EXPIRY_SECONDS // 60} minutes."
        ),
    )
