import pytest
from pytest_celery import CeleryBackendCluster
from pytest_celery import CeleryBrokerCluster
from pytest_celery import RedisTestBackend
from pytest_celery import RedisTestBroker

from tests import tasks


@pytest.fixture
def celery_broker_cluster(celery_redis_broker: RedisTestBroker) -> CeleryBrokerCluster:
    cluster = CeleryBrokerCluster(celery_redis_broker)
    yield cluster
    cluster.teardown()


@pytest.fixture
def celery_backend_cluster(
    celery_redis_backend: RedisTestBackend,
) -> CeleryBackendCluster:
    cluster = CeleryBackendCluster(celery_redis_backend)
    yield cluster
    cluster.teardown()


@pytest.fixture
def default_worker_tasks(default_worker_tasks: set) -> set:

    default_worker_tasks.add(tasks)
    return default_worker_tasks
