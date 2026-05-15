from __future__ import annotations

import pytest
from accounts.tests.factories import UserFactory
from branches.api.views import BranchAdminViewSet
from branches.api.views import BranchViewSet
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory
from rest_framework.test import APIRequestFactory


@pytest.mark.django_db
class TestBranchViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_branch = BranchFactory(school__organization__owner=user)
        foreign_branch = BranchFactory()
        view = BranchViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_branch]
        assert foreign_branch not in queryset

    def test_get_queryset_includes_branch_admin_branch(
        self,
        api_rf: APIRequestFactory,
    ):
        user = UserFactory()
        branch = BranchFactory()
        BranchAdminFactory(user=user, branch=branch)
        foreign_branch = BranchFactory()
        view = BranchViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [branch]
        assert foreign_branch not in queryset


@pytest.mark.django_db
class TestBranchAdminViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_branch_admin = BranchAdminFactory(
            branch__school__organization__owner=user,
        )
        foreign_branch_admin = BranchAdminFactory(
            branch__school__organization__owner=UserFactory(),
        )
        view = BranchAdminViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_branch_admin]
        assert foreign_branch_admin not in queryset

    def test_get_queryset_includes_same_branch_admins(
        self,
        api_rf: APIRequestFactory,
    ):
        user = UserFactory()
        branch_admin = BranchAdminFactory(user=user)
        same_branch_admin = BranchAdminFactory(branch=branch_admin.branch)
        foreign_branch_admin = BranchAdminFactory()
        view = BranchAdminViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert set(queryset) == {branch_admin, same_branch_admin}
        assert foreign_branch_admin not in queryset
