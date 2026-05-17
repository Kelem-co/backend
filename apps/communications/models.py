from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class ChatRoom(UUIDModel, TimeStampedModel):
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="chat_rooms",
        verbose_name=_("Teacher"),
    )
    parent = models.ForeignKey(
        "students.Parent",
        on_delete=models.CASCADE,
        related_name="chat_rooms",
        verbose_name=_("Parent"),
    )

    class Meta:
        verbose_name = _("Chat Room")
        verbose_name_plural = _("Chat Rooms")
        unique_together = ("teacher", "parent")

    def __str__(self):
        return f"Chat: {self.teacher} - {self.parent}"


class Message(UUIDModel, TimeStampedModel):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Room"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name=_("Sender"),
    )
    content = models.TextField(_("Content"))
    is_read = models.BooleanField(_("Is Read"), default=False)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.id} from {self.sender}"


class BroadcastLog(UUIDModel, TimeStampedModel):
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="broadcast_logs",
        verbose_name=_("Teacher"),
    )
    message_body = models.TextField(_("Message Body"))
    recipient_count = models.PositiveIntegerField(_("Recipient Count"))

    class Meta:
        verbose_name = _("Broadcast Log")
        verbose_name_plural = _("Broadcast Logs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Broadcast by {self.teacher} at {self.created_at}"
