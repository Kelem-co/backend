from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Announcement
from .utils import send_priority_notifications


@receiver(post_save, sender=Announcement)
def trigger_urgent_announcement(sender, instance, created, **kwargs):
    """
    Signal to check if an announcement is urgent and trigger the async task.
    We check if it was just created, or if 'is_urgent' was changed to True (simplification: we trigger if it's urgent).
    For a more robust solution, we'd check if 'is_urgent' specifically changed.
    """  # noqa: E501
    if instance.is_urgent and instance.status in [
        Announcement.StatusChoices.SENT,
        Announcement.StatusChoices.SCHEDULED,
    ]:
        send_priority_notifications(instance.id)
