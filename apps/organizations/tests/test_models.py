from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from organizations.models import Organization


def test_organization_str(organization: Organization):
    assert str(organization) == organization.name
