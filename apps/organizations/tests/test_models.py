from __future__ import annotations

import pytest

from organizations.models import Organization


def test_organization_str(organization: Organization):
    assert str(organization) == organization.name
