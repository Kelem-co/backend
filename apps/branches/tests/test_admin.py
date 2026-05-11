from http import HTTPStatus

import pytest
from django.urls import reverse

from branches.models import Branch, BranchAdmin


class TestBranchAdmin:
    def test_changelist(self, admin_client, branch: Branch):
        url = reverse("admin:branches_branch_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:branches_branch_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_branch(self, admin_client, branch: Branch):
        url = reverse("admin:branches_branch_change", kwargs={"object_id": branch.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK


class TestBranchAdminAdmin:  # Testing the BranchAdmin Model Admin
    def test_changelist(self, admin_client, branch_admin: BranchAdmin):
        url = reverse("admin:branches_branchadmin_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:branches_branchadmin_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_view_branch_admin(self, admin_client, branch_admin: BranchAdmin):
        url = reverse("admin:branches_branchadmin_change", kwargs={"object_id": branch_admin.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
