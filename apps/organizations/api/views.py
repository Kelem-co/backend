from organizations.api.serializers import OrganizationSerializer
from organizations.models import Organization
from organizations.services.organization_creation import (
    create_organization_with_verification,
)
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.select_related("owner")
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return self.queryset.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = create_organization_with_verification(
            owner=request.user,
            validated_data=dict(serializer.validated_data),
        )
        response_serializer = self.get_serializer(organization)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
