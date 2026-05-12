from typing import TYPE_CHECKING

import pytest
from organizations.tests.factories import OrganizationFactory

if TYPE_CHECKING:
    from organizations.models import Organization


@pytest.fixture
def organization(db) -> Organization:
    return OrganizationFactory.create()
