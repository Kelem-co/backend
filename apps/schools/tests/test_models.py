from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from schools.models import School


@pytest.mark.django_db
def test_school_str(school: School):
    assert str(school) == school.name
