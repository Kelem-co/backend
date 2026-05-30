from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from core.models import UUIDModel


class ChatThread(UUIDModel, TimeStampedModel):
    parent = models.ForeignKey(
        "students.Parent",
        on_delete=models.CASCADE,
        related_name="chat_threads",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="chat_threads",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="chat_threads",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="chat_threads",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="chat_threads",
    )

    class Meta:
        unique_together = ("parent", "teacher", "student")
        ordering = ["-updated_at"]


class ChatMessage(UUIDModel, TimeStampedModel):
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    text = models.TextField(blank=True)
    attachment = models.ForeignKey(
        "media.MediaFile",
        on_delete=models.SET_NULL,
        related_name="chat_message_attachments",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["created_at"]


class MessageRead(UUIDModel, TimeStampedModel):
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="read_receipts",
    )
    reader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_reads",
    )
    read_at = models.DateTimeField()

    class Meta:
        unique_together = ("message", "reader")
        ordering = ["-read_at"]
