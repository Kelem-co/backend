from organizations.api.serializers import OrganizationSerializer
from organizations.models import Organization
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.select_related("owner")
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
