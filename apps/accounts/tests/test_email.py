from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from accounts.email import ActivationEmail
from accounts.email import ConfirmationEmail
from accounts.email import OrganizationApprovalMagicLinkEmail
from accounts.email import PasswordChangedConfirmationEmail
from accounts.email import PasswordResetEmail
from djoser import utils

if TYPE_CHECKING:
    from accounts.models import User


pytestmark = pytest.mark.django_db


@pytest.fixture
def mocked_email_delay(monkeypatch: pytest.MonkeyPatch, settings) -> Mock:
    settings.DJOSER = {
        **settings.DJOSER,
        "EMAIL_FRONTEND_DOMAIN": None,
        "EMAIL_FRONTEND_PROTOCOL": None,
    }
    delayed_task = Mock()
    monkeypatch.setattr("accounts.email.send_email_task.delay", delayed_task)
    return delayed_task


@pytest.mark.parametrize(
    ("email_class", "expected_subject", "expected_path"),
    [
        (ActivationEmail, "Account activation on Example Site", "activate"),
        (ConfirmationEmail, "Account confirmation on Example Site", None),
        (PasswordResetEmail, "Password reset on Example Site", "reset-password"),
        (
            PasswordChangedConfirmationEmail,
            "Password changed on Example Site",
            None,
        ),
    ],
)
def test_djoser_email_classes_render_multipart_content(
    user: User,
    mocked_email_delay: Mock,
    email_class: type,
    expected_subject: str,
    expected_path: str | None,
):
    message = email_class(
        context={
            "user": user,
            "domain": "example.com",
            "protocol": "https",
            "site_name": "Example Site",
        },
    )

    message.send(["user@example.com"])

    mocked_email_delay.assert_called_once()
    email_fields = mocked_email_delay.call_args.kwargs["email_fields"]
    assert email_fields["subject"] == expected_subject
    assert email_fields["to"] == ["user@example.com"]
    assert email_fields["body"]
    assert email_fields["alternatives"]
    html_body, mime_type = email_fields["alternatives"][0]
    assert mime_type == "text/html"
    assert user.email in email_fields["body"]
    assert user.email in html_body

    if expected_path is not None:
        uid = utils.encode_uid(user.pk)
        assert f"https://example.com/{expected_path}/" in email_fields["body"]
        assert f"https://example.com/{expected_path}/" in html_body
        assert uid in email_fields["body"]
        assert uid in html_body


def test_organization_approval_magic_link_email_renders_multipart_content(
    user: User,
    mocked_email_delay: Mock,
):
    message = OrganizationApprovalMagicLinkEmail(
        context={
            "user": user,
            "organization_name": "Acme Academy",
            "domain": "https://frontend.example.com",
            "protocol": "https",
            "site_name": "Example Site",
            "url": "organization-approval/test-uid/test-token",
        },
    )

    message.send(["user@example.com"])

    mocked_email_delay.assert_called_once()
    email_fields = mocked_email_delay.call_args.kwargs["email_fields"]
    assert email_fields["subject"] == "Organization approved on Example Site"
    assert email_fields["to"] == ["user@example.com"]
    assert "Acme Academy" in email_fields["body"]
    assert "Acme Academy" in email_fields["alternatives"][0][0]
    assert (
        "https://frontend.example.com/organization-approval/test-uid/test-token"
        in email_fields["body"]
    )
