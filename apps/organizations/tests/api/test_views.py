from __future__ import annotations

import pytest
from accounts.tests.factories import UserFactory
from organizations.api.views import OrganizationViewSet
from organizations.tests.factories import OrganizationFactory
from rest_framework.test import APIRequestFactory


@pytest.mark.django_db
class TestOrganizationViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_organization = OrganizationFactory(owner=user)
        foreign_organization = OrganizationFactory()
        view = OrganizationViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_organization]
        assert foreign_organization not in queryset
