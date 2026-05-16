import pytest
from accounts.tasks import get_users_count
from accounts.tasks import send_email_task
from accounts.tests.factories import UserFactory
from celery.result import EagerResult
from django.core import mail

pytestmark = pytest.mark.django_db


def test_user_count(settings):
    """A basic test to execute the get_users_count Celery task."""
    batch_size = 3
    UserFactory.create_batch(batch_size)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    task_result = get_users_count.delay()
    assert isinstance(task_result, EagerResult)
    assert task_result.result == batch_size


def test_send_email_task_attaches_html_alternative():
    result = send_email_task.apply(
        kwargs={
            "email_fields": {
                "subject": "Welcome",
                "body": "Plain body",
                "from_email": "noreply@example.com",
                "to": ["user@example.com"],
                "alternatives": [("<p>HTML body</p>", "text/html")],
            },
        },
    )

    assert result.result == "Email sent to user@example.com"
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.subject == "Welcome"
    assert message.body == "Plain body"
    assert message.alternatives == [("<p>HTML body</p>", "text/html")]
