from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from core.models import ImportJob
from core.api.serializers import ImportJobSerializer

@extend_schema(
    summary="Get Bulk Import Job Status",
    description="Retrieve the status, progress, and errors of a bulk import job.",
)
class ImportStatusView(generics.RetrieveAPIView):
    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "task_id"
