from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import NoReverseMatch
from django.urls import Resolver404
from django.urls import resolve
from django.urls import reverse

if TYPE_CHECKING:
    from kelem_co_backend.users.models import User


def test_admin_index_url():
    assert reverse("admin:index") == "/admin/"
    assert resolve("/admin/").view_name == "admin:index"


def test_removed_user_ui_urls_are_not_registered(user: User):
    with pytest.raises(NoReverseMatch):
        reverse("users:detail", kwargs={"username": user.username})

    with pytest.raises(NoReverseMatch):
        reverse("users:update")

    with pytest.raises(NoReverseMatch):
        reverse("users:redirect")


def test_removed_public_ui_paths_do_not_resolve():
    for path in ["/", "/about/", "/users/", "/accounts/login/"]:
        with pytest.raises(Resolver404):
            resolve(path)


def test_api_urls_remain_registered(user: User):
    assert reverse("api:list_users") == "/api/users/"
    assert reverse("api:retrieve_user", kwargs={"username": user.username}) == (
        f"/api/users/{user.username}/"
    )
