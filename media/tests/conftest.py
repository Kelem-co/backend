from __future__ import annotations

import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


def pytest_configure():
    if not settings.configured:
        django.setup()
