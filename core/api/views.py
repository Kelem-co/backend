from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.api.access import scope_queryset_for_user
from core.api.serializers import ImportJobSerializer
from core.models import ImportJob


@extend_schema(
    summary="Get Bulk Import Job Status",
    description="Retrieve the status, progress, and errors of a bulk import job.",
)
class ImportStatusView(generics.RetrieveAPIView):
    serializer_class = ImportJobSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        return scope_queryset_for_user(ImportJob.objects.all(), self.request.user)
