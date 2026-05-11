import pytest

from schools.tests.factories import SchoolFactory


@pytest.fixture
def school(db) -> "School":
    return SchoolFactory.create()
