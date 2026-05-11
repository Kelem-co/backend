from http import HTTPStatus

import pytest
from django.urls import reverse

from schools.models import School


class TestSchoolAdmin:
    def test_changelist(self, admin_client, school: School):
        url = reverse("admin:schools_school_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:schools_school_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_school(self, admin_client, school: School):
        url = reverse("admin:schools_school_change", kwargs={"object_id": school.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
