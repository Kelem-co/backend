from __future__ import annotations

import pytest

from schools.models import School


@pytest.mark.django_db
def test_school_str(school: School):
    assert str(school) == school.name
