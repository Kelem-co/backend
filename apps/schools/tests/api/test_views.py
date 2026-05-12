from __future__ import annotations

import pytest
from accounts.tests.factories import UserFactory
from rest_framework.test import APIRequestFactory
from schools.api.views import SchoolViewSet
from schools.tests.factories import SchoolFactory


@pytest.mark.django_db
class TestSchoolViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset_scopes_to_request_owner(self, api_rf: APIRequestFactory):
        user = UserFactory()
        owned_school = SchoolFactory(organization__owner=user)
        foreign_school = SchoolFactory()
        view = SchoolViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [owned_school]
        assert foreign_school not in queryset
