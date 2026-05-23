"""
Signals for the academics app.

post_save on Branch
  When a new Branch is created, automatically create the current
  Ethiopian academic year for it so the branch is immediately usable.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="branches.Branch")
def create_academic_year_for_new_branch(sender, instance, created, **kwargs):
    """
    Auto-create the current academic year whenever a new Branch is saved.
    Skipped on updates — the Celery beat task handles annual rollovers.
    """
    if not created:
        return

    from .utils import get_or_create_academic_year_for_branch  # noqa: PLC0415

    try:
        year, was_created = get_or_create_academic_year_for_branch(instance)
        logger.info(
            "Auto-created academic year '%s' for new branch '%s' (created=%s)",
            year.name,
            instance.name,
            was_created,
        )
    except Exception:
        # Never let a signal failure block branch creation
        logger.exception(
            "Failed to auto-create academic year for branch '%s'",
            instance.name,
        )
