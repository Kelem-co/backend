"""
Utility helpers for the academics app.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from branches.models import Branch

    from .models import AcademicYear

logger = logging.getLogger(__name__)


ACADEMIC_YEAR_START_MONTH = 9  # September


def current_ethiopian_academic_year_dates(
    reference_date: datetime.date | None = None,
) -> tuple[str, datetime.date, datetime.date]:
    """
    Return (name, start_date, end_date) for the Ethiopian academic year
    that contains *reference_date* (defaults to today).

    Ethiopian academic year:
      - Starts September 1
      - Ends July 31 of the following calendar year
      - Named "YYYY/YYYY+1"  e.g. "2024/2025"

    Examples
    --------
    reference_date = 2024-10-15  →  ("2024/2025", 2024-09-01, 2025-07-31)
    reference_date = 2025-03-20  →  ("2024/2025", 2024-09-01, 2025-07-31)
    reference_date = 2025-09-01  →  ("2025/2026", 2025-09-01, 2026-07-31)
    """
    if reference_date is None:
        reference_date = timezone.now().date()

    # If we are in September or later the new year has started
    if reference_date.month >= ACADEMIC_YEAR_START_MONTH:
        start_year = reference_date.year
    else:
        start_year = reference_date.year - 1

    end_year = start_year + 1
    name = f"{start_year}/{end_year}"
    start_date = datetime.date(start_year, 9, 1)
    end_date = datetime.date(end_year, 7, 31)
    return name, start_date, end_date


@transaction.atomic
def get_or_create_academic_year_for_branch(
    branch: Branch,
    reference_date: datetime.date | None = None,
) -> tuple[AcademicYear, bool]:
    """
    Ensure the current Ethiopian academic year exists for *branch*.

    - Creates the record if it does not exist.
    - Marks it as ``is_current = True``.
    - Marks all other academic years for the same branch as
      ``is_current = False``.

    Returns (academic_year, was_created).
    """
    from .models import AcademicYear  # noqa: PLC0415

    name, start_date, end_date = current_ethiopian_academic_year_dates(reference_date)

    year, was_created = AcademicYear.objects.get_or_create(
        branch=branch,
        name=name,
        defaults={
            "organization": branch.organization,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": True,
        },
    )

    # Retire all other years for this branch
    AcademicYear.objects.filter(branch=branch).exclude(pk=year.pk).update(
        is_current=False,
    )

    # If the year already existed but wasn't marked current, fix it
    if not was_created and not year.is_current:
        year.is_current = True
        year.save(update_fields=["is_current", "updated_at"])

    logger.info(
        "Academic year '%s' for branch '%s' — created=%s",
        name,
        branch.name,
        was_created,
    )
    return year, was_created
