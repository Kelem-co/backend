from http import HTTPStatus

import pytest
from django.urls import reverse

from schools.models import Branch, BranchAdmin, School


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


class TestBranchAdmin:
    def test_changelist(self, admin_client, branch: Branch):
        url = reverse("admin:schools_branch_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:schools_branch_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_branch(self, admin_client, branch: Branch):
        url = reverse("admin:schools_branch_change", kwargs={"object_id": branch.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK


class TestBranchAdminAdmin:  # Testing the BranchAdmin Model Admin
    def test_changelist(self, admin_client, branch_admin: BranchAdmin):
        url = reverse("admin:schools_branchadmin_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:schools_branchadmin_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_branch_admin(self, admin_client, branch_admin: BranchAdmin):
        url = reverse("admin:schools_branchadmin_change", kwargs={"object_id": branch_admin.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
