from typing import TYPE_CHECKING

import pytest
from schools.tests.factories import SchoolFactory

if TYPE_CHECKING:
    from schools.models import School


@pytest.fixture
def school(db) -> School:
    return SchoolFactory.create()
