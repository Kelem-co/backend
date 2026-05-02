from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_celery import CeleryTestSetup


def test_hello_world(celery_setup: CeleryTestSetup):
    assert celery_setup.ready()
