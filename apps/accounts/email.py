from __future__ import annotations

from email.header import Header
from typing import TYPE_CHECKING
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings as django_settings
from django.template.loader import render_to_string
from djoser import email

from .tasks import send_email_task

if TYPE_CHECKING:
    from collections.abc import Sequence


def _template_path(stem: str, suffix: str) -> str:
    return f"email/{stem}{suffix}"


class AsyncMultipartDjoserEmail(email.BaseDjoserEmail):
    template_stem: str

    def render_email_parts(self) -> dict[str, Any]:
        context = self.get_context_data()
        if url := context.get("url"):
            domain = str(context["domain"]).rstrip("/")
            parsed_domain = urlsplit(domain)
            if parsed_domain.scheme and parsed_domain.netloc:
                base_url = domain
            else:
                base_url = f"{context['protocol']}://{domain}"
            context["full_url"] = f"{base_url}/{url}"
        subject = render_to_string(
            _template_path(self.template_stem, "_subject.txt"),
            context,
        ).strip()
        body = render_to_string(
            _template_path(self.template_stem, "_body.txt"),
            context,
        ).strip()
        html_body = render_to_string(
            _template_path(self.template_stem, "_body.html"),
            context,
        ).strip()
        return {
            "subject": str(Header(subject, "utf-8")).replace("\n", ""),
            "body": body,
            "alternatives": [(html_body, "text/html")],
        }

    def send(
        self,
        to: Sequence[str],
        fail_silently: bool = False,  # noqa: FBT001, FBT002
        **kwargs: Any,
    ) -> None:
        email_fields = self.render_email_parts()
        email_fields.update(
            {
                "to": list(to),
                "cc": kwargs.pop("cc", []),
                "bcc": kwargs.pop("bcc", []),
                "reply_to": kwargs.pop("reply_to", []),
                "from_email": kwargs.pop(
                    "from_email",
                    django_settings.DEFAULT_FROM_EMAIL,
                ),
                "fail_silently": fail_silently,
            },
        )
        self.request = None
        send_email_task.delay(email_fields=email_fields)


class ActivationEmail(AsyncMultipartDjoserEmail, email.ActivationEmail):
    template_stem = "activation"


class ConfirmationEmail(AsyncMultipartDjoserEmail, email.ConfirmationEmail):
    template_stem = "confirmation"


class PasswordResetEmail(AsyncMultipartDjoserEmail, email.PasswordResetEmail):
    template_stem = "password_reset"


class PasswordChangedConfirmationEmail(
    AsyncMultipartDjoserEmail,
    email.PasswordChangedConfirmationEmail,
):
    template_stem = "password_changed_confirmation"


class BranchAdminInvitationEmail(AsyncMultipartDjoserEmail):
    template_stem = "branch_admin_invitation"


class TeacherInvitationEmail(AsyncMultipartDjoserEmail):
    template_stem = "teacher_invitation"


class OrganizationApprovalMagicLinkEmail(AsyncMultipartDjoserEmail):
    template_stem = "organization_approval_magic_link"
