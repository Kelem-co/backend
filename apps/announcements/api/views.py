from academics.models import Grade
from academics.models import Section
from announcements.models import Announcement
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.access import scope_queryset_for_user

from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    CRUD for the Announcement mapping.
    Supports filtering by ?status=DRAFT and ?target_roles=PARENTS via query params,
    and text search via ?search=.
    """

    queryset = Announcement.objects.prefetch_related(
        "targeted_grades",
        "targeted_sections",
    ).all()
    serializer_class = AnnouncementSerializer
    lookup_field = "id"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject", "message"]
    ordering_fields = ["created_at", "scheduled_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        # Rule 2: Tenant isolation via branch_id
        # Assuming the scope_queryset_for_user automatically scopes based on user's branch
        qs = scope_queryset_for_user(self.queryset, self.request.user)

        # Manual filtering
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        target_roles = self.request.query_params.get("target_roles")
        if target_roles:
            qs = qs.filter(target_roles=target_roles)

        is_urgent = self.request.query_params.get("is_urgent")
        if is_urgent is not None:
            qs = qs.filter(
                is_urgent=is_urgent.lower() in ["true", "1", "t", "y", "yes"],
            )

        branch_id = self.request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        organization_id = self.request.query_params.get("organization")
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        return qs

    @action(detail=False, methods=["get"])
    def get_targeting_criteria(self, request):
        """
        Returns the available Grades and Sections for the Admin’s branch.
        """
        user = request.user

        # We need to get the grades and sections for the user's branch.
        # Assuming scope_queryset_for_user helps us scope it correctly.
        grades = scope_queryset_for_user(Grade.objects.all(), user)
        sections = scope_queryset_for_user(
            Section.objects.select_related("grade").all(),
            user,
        )

        # Serialize the data simply to return as JSON
        grade_data = [
            {"id": str(g.id), "name": g.name, "level": g.level} for g in grades
        ]
        section_data = [
            {
                "id": str(s.id),
                "name": s.name,
                "grade_name": s.grade.name if s.grade else None,
            }
            for s in sections
        ]

        return Response(
            {
                "grades": grade_data,
                "sections": section_data,
            },
        )
