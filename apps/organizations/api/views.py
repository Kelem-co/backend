from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from organizations.models import Organization
from organizations.api.serializers import OrganizationSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    # Future: get_queryset can filter by requesting user role once RBAC is fully implemented.
