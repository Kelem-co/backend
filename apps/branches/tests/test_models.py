from __future__ import annotations

import pytest

from branches.models import Branch, BranchAdmin


@pytest.mark.django_db
def test_branch_str(branch: Branch):
    assert str(branch) == f"{branch.school.name} - {branch.name}"


@pytest.mark.django_db
def test_branch_admin_str(branch_admin: BranchAdmin):
    assert str(branch_admin) == f"{branch_admin.user.name} - {branch_admin.branch.name}"
