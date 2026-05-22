from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from schools.api.serializers import SchoolSerializer
from schools.models import School


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.select_related(
        "organization",
        "organization__owner",
        "logo",
    )
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["organization", "branches"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return self.queryset.filter(organization__owner=self.request.user)
