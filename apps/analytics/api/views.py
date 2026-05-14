from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from analytics.models import InterventionLog
from .serializers import InterventionLogSerializer


class InterventionLogViewSet(viewsets.ModelViewSet):
    """
    CRUD for Intervention Logs.

    Records are auto-created by signals (e.g. low grade detection).
    Staff can update status (OPEN → IN_PROGRESS → RESOLVED) and add notes.

    Filters:
      ?organization=<id>
      ?student=<id>
      ?intervention_type=LOW_GRADE|ATTENDANCE|BEHAVIOUR|OTHER
      ?severity=LOW|MEDIUM|HIGH|CRITICAL
      ?status=OPEN|IN_PROGRESS|RESOLVED|DISMISSED

    Text search (?search=):
      Student name, title, description
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    serializer_class = InterventionLogSerializer
    filter_backends = [SearchFilter]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "title",
        "description",
    ]

    def get_queryset(self):
        qs = InterventionLog.objects.select_related("student", "organization")
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("student"):
            qs = qs.filter(student_id=p["student"])
        if p.get("intervention_type"):
            qs = qs.filter(intervention_type=p["intervention_type"].upper())
        if p.get("severity"):
            qs = qs.filter(severity=p["severity"].upper())
        if p.get("status"):
            qs = qs.filter(status=p["status"].upper())
        return qs
