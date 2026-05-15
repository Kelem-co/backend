from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def add_user_to_group(sender, instance, created, **kwargs):
    if created and instance.role:
        group_name = instance.role
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
