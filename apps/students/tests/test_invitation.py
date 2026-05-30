from __future__ import annotations

from unittest.mock import patch

import pytest
from accounts.models import User
from accounts.tests.factories import UserFactory
from branches.tests.factories import BranchAdminFactory
from branches.tests.factories import BranchFactory
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIRequestFactory
from students.api.views import ParentCompleteInvitationView
from students.api.views import ParentInviteView
from students.models import Parent


@pytest.mark.django_db
class TestParentInviteView:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @patch("students.api.views.send_parent_invitation_sms")
    def test_invite_success(self, mock_send_sms, api_rf: APIRequestFactory):
        user = UserFactory()
        branch = BranchFactory(school__organization__owner=user)

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "New",
                "father_name": "Parent",
                "grandfather_name": "Test",
                "phone_number": "+251911111201",
                "branch": branch.id,
            },
        )
        request.user = user

        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Parent invitation sent successfully."
        assert "/complete-parent-invitation/" in response.data["invitation_url"]

        parent_user = User.objects.get(phone_number="+251911111201")
        assert parent_user.role == User.Role.PARENT
        assert parent_user.is_active is False

        parent = Parent.objects.get(user=parent_user)
        assert parent.is_active is False
        assert branch.organization in parent.organizations.all()
        assert branch in parent.branches.all()
        mock_send_sms.assert_called_once()

    @patch("students.api.views.send_parent_invitation_sms")
    def test_reinvite_updates_existing_inactive_parent(
        self,
        mock_send_sms,
        api_rf: APIRequestFactory,
    ):
        owner = UserFactory()
        old_branch = BranchFactory(school__organization__owner=owner)
        new_branch = BranchFactory(school__organization__owner=owner)
        user = UserFactory(
            role=User.Role.PARENT,
            is_active=False,
            phone_number="+251911111202",
            name="Old",
            father_name="Parent",
            grandfather_name="Name",
        )
        parent = Parent.objects.create(
            user=user,
            occupation="Old Occupation",
            is_active=False,
        )
        parent.organizations.add(old_branch.organization)
        parent.branches.add(old_branch)

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "Updated",
                "father_name": "Parent",
                "grandfather_name": "Profile",
                "phone_number": "+251911111202",
                "occupation": "Engineer",
                "branch": new_branch.id,
            },
        )
        request.user = owner

        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        user.refresh_from_db()
        parent.refresh_from_db()
        assert User.objects.filter(phone_number="+251911111202").count() == 1
        assert user.name == "Updated"
        assert user.is_active is False
        assert parent.occupation == "Engineer"
        assert parent.is_active is False
        assert list(parent.organizations.all()) == [new_branch.organization]
        assert list(parent.branches.all()) == [new_branch]
        mock_send_sms.assert_called_once()

    def test_invite_rejects_existing_active_parent(self, api_rf: APIRequestFactory):
        owner = UserFactory()
        branch = BranchFactory(school__organization__owner=owner)
        user = UserFactory(
            role=User.Role.PARENT,
            is_active=True,
            phone_number="+251911111203",
        )
        parent = Parent.objects.create(user=user)
        parent.organizations.add(branch.organization)
        parent.branches.add(branch)

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "Active",
                "father_name": "Parent",
                "grandfather_name": "User",
                "phone_number": "+251911111203",
                "branch": branch.id,
            },
        )
        request.user = owner

        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["errors"][0]["field"] == "phone_number"

    def test_invite_rejects_existing_user_with_wrong_role(
        self,
        api_rf: APIRequestFactory,
    ):
        owner = UserFactory()
        branch = BranchFactory(school__organization__owner=owner)
        UserFactory(
            role=User.Role.TEACHER,
            is_active=False,
            phone_number="+251911111204",
        )

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "Wrong",
                "father_name": "Role",
                "grandfather_name": "User",
                "phone_number": "+251911111204",
                "branch": branch.id,
            },
        )
        request.user = owner

        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["errors"][0]["field"] == "phone_number"

    @patch(
        "students.api.views.send_parent_invitation_sms",
        side_effect=RuntimeError("boom"),
    )
    def test_invite_rolls_back_when_sms_send_fails(
        self,
        mock_send_sms,
        api_rf: APIRequestFactory,
    ):
        owner = UserFactory()
        branch = BranchFactory(school__organization__owner=owner)

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "Rollback",
                "father_name": "Parent",
                "grandfather_name": "Case",
                "phone_number": "+251911111205",
                "branch": branch.id,
            },
        )
        request.user = owner

        with pytest.raises(RuntimeError, match="boom"):
            view(request)

        assert mock_send_sms.called
        assert not User.objects.filter(phone_number="+251911111205").exists()

    def test_invite_allows_active_branch_admin_for_own_branch(
        self,
        api_rf: APIRequestFactory,
    ):
        branch_admin_user = UserFactory()
        branch = BranchFactory()
        BranchAdminFactory(
            user=branch_admin_user,
            branch=branch,
            organization=branch.organization,
        )

        view = ParentInviteView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {
                "name": "Branch",
                "father_name": "Admin",
                "grandfather_name": "Parent",
                "phone_number": "+251911111206",
                "branch": branch.id,
            },
        )
        request.user = branch_admin_user

        with patch("students.api.views.send_parent_invitation_sms") as mock_send_sms:
            response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert mock_send_sms.called


@pytest.mark.django_db
class TestParentCompleteInvitationView:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_complete_success(self, api_rf: APIRequestFactory):
        user = UserFactory(
            role=User.Role.PARENT,
            is_active=False,
            phone_number="+251911111207",
        )
        Parent.objects.create(user=user, is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        view = ParentCompleteInvitationView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {"uid": uid, "token": token},
        )

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True
        assert user.verified_at is not None
        assert user.parent_profile.is_active is True

    def test_complete_invalid_token(self, api_rf: APIRequestFactory):
        user = UserFactory(
            role=User.Role.PARENT,
            is_active=False,
            phone_number="+251911111208",
        )
        Parent.objects.create(user=user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        view = ParentCompleteInvitationView.as_view()
        request = api_rf.post(
            "/fake-url/",
            {"uid": uid, "token": "invalid-token"},
        )

        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["errors"][0]["field"] == "token"
