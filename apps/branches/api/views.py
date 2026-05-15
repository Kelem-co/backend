from branches.api.serializers import BranchAdminSerializer
from branches.api.serializers import BranchSerializer
from branches.models import Branch
from branches.models import BranchAdmin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.api.access import scope_queryset_for_user


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related(
        "organization",
        "organization__owner",
        "school",
    )
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(
            self.queryset,
            self.request.user,
            branch_lookup="self",
        )


class BranchAdminViewSet(viewsets.ModelViewSet):
    queryset = BranchAdmin.objects.select_related(
        "organization",
        "organization__owner",
        "branch",
        "user",
    )
    serializer_class = BranchAdminSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(self.queryset, self.request.user)
