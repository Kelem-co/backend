import pytest

from branches.tests.factories import BranchAdminFactory, BranchFactory


@pytest.fixture
def branch(db) -> "Branch":
    return BranchFactory.create()


@pytest.fixture
def branch_admin(db) -> "BranchAdmin":
    return BranchAdminFactory.create()
