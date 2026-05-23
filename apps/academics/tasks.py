"""
Celery tasks for the academics app.

rollover_academic_years
  Runs every year on September 1st (Ethiopian academic year start).
  For every active branch it ensures the new academic year record exists
  and marks it as current, retiring the previous one.
"""

import logging

from celery import shared_task
from django.db import DatabaseError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def rollover_academic_years(self):
    """
    Create the new Ethiopian academic year for every active branch and
    mark it as current.  Safe to run multiple times — uses get_or_create
    so duplicate records are never produced.

    Scheduled: annually on September 1st via django-celery-beat.
    Can also be triggered manually from the Django shell:
        from academics.tasks import rollover_academic_years
        rollover_academic_years.delay()
    """
    from branches.models import Branch  # noqa: PLC0415

    from .utils import get_or_create_academic_year_for_branch  # noqa: PLC0415

    branches = Branch.objects.filter(status=Branch.Status.ACTIVE).select_related(
        "organization",
    )

    created_count = 0
    updated_count = 0
    error_count = 0

    for branch in branches:
        try:
            _year, was_created = get_or_create_academic_year_for_branch(branch)
            if was_created:
                created_count += 1
            else:
                updated_count += 1
        except DatabaseError as exc:
            logger.exception(
                "Failed to rollover academic year for branch %s",
                branch.id,
            )
            error_count += 1

    logger.info(
        "Academic year rollover complete — created: %d, updated: %d, errors: %d",
        created_count,
        updated_count,
        error_count,
    )
    return {
        "created": created_count,
        "updated": updated_count,
        "errors": error_count,
    }
