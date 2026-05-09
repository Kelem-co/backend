from __future__ import annotations

import typing

from django.conf import settings as django_settings
from djoser import email

from .tasks import send_email_task


class AsyncDjoserEmailMessage(email.BaseDjoserEmail):
    @typing.override
    def send(self, to, fail_silently=False, **kwargs):
        self.render()

        self.to = to
        self.cc = kwargs.pop("cc", [])
        self.bcc = kwargs.pop("bcc", [])
        self.reply_to = kwargs.pop("reply_to", [])
        self.from_email = kwargs.pop("from_email", django_settings.DEFAULT_FROM_EMAIL)
        self.request = None

        send_email_task.delay(
            email_fields={
                "subject": self.subject,
                "body": self.body,
                "from_email": self.from_email,
                "to": self.to,
                "bcc": self.bcc,
                "cc": self.cc,
                "reply_to": self.reply_to,
                "alternatives": self.alternatives,
            },
        )


class ActivationEmail(email.ActivationEmail, AsyncDjoserEmailMessage):
    template_name = "email/activation.html"


class PasswordResetEmail(email.PasswordResetEmail, AsyncDjoserEmailMessage):
    template_name = "email/password_reset.html"


class PasswordChangedConfirmationEmail(
    AsyncDjoserEmailMessage,
    email.PasswordChangedConfirmationEmail,
):
    template_name = "email/password_changed_confirmation.html"


class ConfirmationEmail(AsyncDjoserEmailMessage, email.ConfirmationEmail):
    template_name = "email/confirmation.html"
