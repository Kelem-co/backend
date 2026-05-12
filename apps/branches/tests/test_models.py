from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from branches.models import Branch
    from branches.models import BranchAdmin


@pytest.mark.django_db
def test_branch_str(branch: Branch):
    assert str(branch) == f"{branch.school.name} - {branch.name}"


@pytest.mark.django_db
def test_branch_admin_str(branch_admin: BranchAdmin):
    assert str(branch_admin) == f"{branch_admin.user.name} - {branch_admin.branch.name}"
