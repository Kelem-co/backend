from typing import TYPE_CHECKING

import pytest
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory

if TYPE_CHECKING:
    from branches.models import Branch
    from branches.models import BranchAdmin


@pytest.fixture
def branch(db) -> Branch:
    return BranchFactory.create()


@pytest.fixture
def branch_admin(db) -> BranchAdmin:
    return BranchAdminFactory.create()
