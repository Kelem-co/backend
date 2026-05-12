from typing import TYPE_CHECKING

import pytest
from accounts.models import User
from accounts.tests.factories import UserFactory

if TYPE_CHECKING:
    from accounts.models import User


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()
