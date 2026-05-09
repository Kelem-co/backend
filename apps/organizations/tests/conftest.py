import pytest

from organizations.tests.factories import OrganizationFactory

@pytest.fixture
def organization(db) -> "Organization":
    return OrganizationFactory.create()
