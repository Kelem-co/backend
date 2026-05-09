import pytest

from schools.tests.factories import BranchAdminFactory, BranchFactory, SchoolFactory


@pytest.fixture
def school(db) -> "School":
    return SchoolFactory.create()


@pytest.fixture
def branch(db) -> "Branch":
    return BranchFactory.create()


@pytest.fixture
def branch_admin(db) -> "BranchAdmin":
    return BranchAdminFactory.create()
