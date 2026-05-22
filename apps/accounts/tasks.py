from __future__ import annotations

from typing import Any

from celery import shared_task
from django.core.mail import EmailMultiAlternatives

from .models import User


@shared_task()
def get_users_count() -> int:
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_fields: dict[str, Any]) -> str:
    email_message = EmailMultiAlternatives(
        subject=email_fields["subject"],
        body=email_fields["body"],
        from_email=email_fields["from_email"],
        to=email_fields["to"],
        bcc=email_fields.get("bcc", []),
        cc=email_fields.get("cc", []),
        reply_to=email_fields.get("reply_to", []),
    )

    for alternative in email_fields.get("alternatives", []):
        email_message.attach_alternative(*alternative)

    try:
        email_message.send(
            fail_silently=email_fields.get("fail_silently", False),
        )
    except Exception as exc:
        retry_delay = 2**self.request.retries
        raise self.retry(exc=exc, countdown=retry_delay) from exc

    return f"Email sent to {', '.join(email_message.to)}"
