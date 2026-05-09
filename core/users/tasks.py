from __future__ import annotations

from celery import shared_task
from django.core.mail import EmailMultiAlternatives

from .models import User


@shared_task()
def get_users_count() -> int:
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_fields: dict):
    try:
        email = EmailMultiAlternatives(
            subject=email_fields["subject"],
            body=email_fields["body"],
            from_email=email_fields["from_email"],
            to=email_fields["to"],
            bcc=email_fields.get("bcc", []),
            cc=email_fields.get("cc", []),
            reply_to=email_fields.get("reply_to", []),
        )

        if email_fields.get("alternatives"):
            for alt in email_fields["alternatives"]:
                email.attach_alternative(*alt)

        email.send(fail_silently=False)
    except Exception as exc:
        retry_delay = 2**self.request.retries

        raise self.retry(exc=exc, countdown=retry_delay) from exc
    else:
        return f"Email sent to {email.to}"
