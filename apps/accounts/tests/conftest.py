import pytest

from accounts.tests.factories import UserFactory

@pytest.fixture
def user(db) -> "User":
    return UserFactory.create()
