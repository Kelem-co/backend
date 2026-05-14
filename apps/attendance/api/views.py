from django.db import transaction, IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from attendance.models import Attendance, AttendanceReason, AttendanceSummary
from .serializers import (
    AttendanceSerializer,
    AttendanceReadSerializer,
    AttendanceReasonSerializer,
    AttendanceReasonReadSerializer,
    BulkAttendanceSerializer,
    ParentReasonUpdateSerializer,
    AttendanceSummarySerializer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tenant_qs(qs, request):
    """
    Filter any queryset down to the requesting user's organization(s).
    Adapt this to your RBAC / tenant-lookup strategy.
    """
    if getattr(request, "query_params", None):
        org = request.query_params.get("organization")
        if org:
            return qs.filter(organization_id=org)
    return qs


# ---------------------------------------------------------------------------
# Attendance ViewSet
# ---------------------------------------------------------------------------

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for individual attendance records.

    Query-param filters:
      ?organization=<id>   Tenant filter (required in production)
      ?branch=<id>
      ?section=<id>
      ?student=<id>
      ?academic_year=<id>
      ?date=YYYY-MM-DD
      ?status=PRESENT|ABSENT|LATE|EXCUSED

    Text search (?search=):
      Student first/last name, roll number, section name

    Custom actions:
      POST /attendance/bulk-submit/
          Teacher submits a full section's attendance for one day.

      GET  /attendance/by-section/?section=<id>&date=YYYY-MM-DD
          All records for a section on a given date.

      GET  /attendance/by-student/?student=<id>[&academic_year=<id>]
          Full attendance history for one student.

      GET  /attendance/daily-status/
          All attendance records for a chosen date (default: today).
          Filter further by ?status=ABSENT|LATE|EXCUSED|PRESENT,
          ?section=, ?branch=, ?organization=.
          Returns full student details in every record.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__roll_no",
        "section__name",
    ]

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            "student",
            "section__grade",
            "academic_year",
            "branch",
            "organization",
            "recorded_by",
            "reason",
        )
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("branch"):
            qs = qs.filter(branch_id=p["branch"])
        if p.get("section"):
            qs = qs.filter(section_id=p["section"])
        if p.get("student"):
            qs = qs.filter(student_id=p["student"])
        if p.get("academic_year"):
            qs = qs.filter(academic_year_id=p["academic_year"])
        if p.get("date"):
            qs = qs.filter(date=p["date"])
        if p.get("status"):
            qs = qs.filter(status=p["status"].upper())
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "by_section", "by_student", "daily_status"]:
            return AttendanceReadSerializer
        return AttendanceSerializer

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

    # ------------------------------------------------------------------
    # POST /attendance/bulk-submit/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-submit")
    def bulk_submit(self, request):
        """
        Teacher submits attendance for an entire section in one request.

        - Idempotent: records already matched by (student, date, section)
          are skipped (not errored), supporting PWA offline sync.
        - client_side_id: if provided per item, is stored for dedup.
        - Fires the post_save signal for each created record, which
          queues parent notifications and summary updates.
        """
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        section = data["section"]
        academic_year = data["academic_year"]
        organization = data["organization"]
        branch = data["branch"]
        date = data["date"]

        created_ids = []
        skipped = []
        errors = []

        with transaction.atomic():
            for item in data["records"]:
                try:
                    obj, was_created = Attendance.objects.get_or_create(
                        student=item["student"],
                        date=date,
                        section=section,
                        defaults={
                            "academic_year": academic_year,
                            "organization": organization,
                            "branch": branch,
                            "recorded_by": request.user,
                            "status": item["status"],
                            "remarks": item.get("remarks", ""),
                            "client_side_id": item.get("client_side_id", None) or __import__("uuid").uuid4(),
                        },
                    )
                    if was_created:
                        created_ids.append(str(obj.id))
                    else:
                        skipped.append(str(obj.id))
                except IntegrityError as exc:
                    errors.append({
                        "student": str(item["student"].id),
                        "error": str(exc),
                    })

        return Response(
            {
                "created": len(created_ids),
                "skipped": len(skipped),
                "errors": errors,
                "created_ids": created_ids,
            },
            status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # GET /attendance/by-section/?section=<id>&date=YYYY-MM-DD
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
    def by_section(self, request):
        """
        Returns all attendance records for a section on a given date.
        Required: ?section=<uuid>&date=YYYY-MM-DD
        """
        section_id = request.query_params.get("section")
        date = request.query_params.get("date")
        if not section_id or not date:
            return Response(
                {"detail": "Both 'section' and 'date' query params are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(section_id=section_id, date=date)
        qs = self.filter_queryset(qs)
        serializer = AttendanceReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /attendance/by-student/?student=<id>[&academic_year=<id>]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-student")
    def by_student(self, request):
        """
        Full attendance history for one student.
        Required: ?student=<uuid>
        Optional: ?academic_year=<uuid>, ?status=
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response(
                {"detail": "Query parameter 'student' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(student_id=student_id)
        qs = self.filter_queryset(qs)
        serializer = AttendanceReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /attendance/daily-status/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="daily-status")
    def daily_status(self, request):
        """
        Returns attendance records for a specific date, defaulting to today.

        Query params:
          ?date=YYYY-MM-DD   Target date (default: today / server local date)
          ?status=ABSENT     Filter by status: ABSENT, LATE, EXCUSED, PRESENT
                             (can be repeated: ?status=ABSENT&status=LATE)
          ?section=<id>      Narrow to one section
          ?branch=<id>       Narrow to one branch
          ?organization=<id> Tenant filter
          ?search=           Text search on student name / roll no

        Response includes full student details:
          student name, roll_no, photo, section, grade, branch,
          status, remarks, reason (if any), and recorded_by.
        """
        from django.utils import timezone

        # Resolve the target date (default = today)
        date_param = request.query_params.get("date")
        if date_param:
            target_date = date_param          # validated by DB if malformed
        else:
            target_date = timezone.localdate()

        qs = self.get_queryset().filter(date=target_date)

        # Multi-value status filter: ?status=ABSENT&status=LATE
        statuses = request.query_params.getlist("status")
        if statuses:
            qs = qs.filter(status__in=[s.upper() for s in statuses])

        # Additional narrowing — section / branch / org already handled
        # by get_queryset() but we re-apply here for the dedicated endpoint
        p = request.query_params
        if p.get("section"):
            qs = qs.filter(section_id=p["section"])
        if p.get("branch"):
            qs = qs.filter(branch_id=p["branch"])
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])

        qs = self.filter_queryset(qs)          # applies ?search=
        qs = qs.select_related(
            "student__current_section__grade",
            "student__branch",
            "reason",
        )

        serializer = AttendanceReadSerializer(qs, many=True)
        return Response({
            "date": str(target_date),
            "count": qs.count(),
            "results": serializer.data,
        })


# ---------------------------------------------------------------------------
# AttendanceReason ViewSet
# ---------------------------------------------------------------------------

class AttendanceReasonViewSet(viewsets.ModelViewSet):
    """
    CRUD for attendance reasons.

    The standard create/update/delete is available for admin/teacher use.

    Parent-specific update endpoint:
      PATCH /attendance-reasons/<id>/parent-update/
          Restricted to the fields a parent is allowed to change:
          reason_category, note, parent_confirmed.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "attendance__student__first_name",
        "attendance__student__last_name",
        "reason_category",
    ]

    def get_queryset(self):
        qs = AttendanceReason.objects.select_related(
            "attendance__student",
            "attendance__section",
            "attendance__academic_year",
            "organization",
            "confirmed_by",
        )
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("attendance"):
            qs = qs.filter(attendance_id=p["attendance"])
        if p.get("student"):
            qs = qs.filter(attendance__student_id=p["student"])
        if p.get("parent_confirmed"):
            val = p["parent_confirmed"].lower() in ("true", "1", "yes")
            qs = qs.filter(parent_confirmed=val)
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AttendanceReasonReadSerializer
        if self.action == "parent_update":
            return ParentReasonUpdateSerializer
        return AttendanceReasonSerializer

    # ------------------------------------------------------------------
    # PATCH /attendance-reasons/<id>/parent-update/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["patch"], url_path="parent-update")
    def parent_update(self, request, id=None):
        """
        Parent-only endpoint to provide / confirm an absence reason.
        Only allows editing: reason_category, note, parent_confirmed.

        TODO: Add a permission class to restrict this to the student's
              linked parents (check ParentStudentLink).
        """
        reason = self.get_object()

        # Guard: reason must be for a non-PRESENT attendance
        if not reason.attendance.needs_reason:
            return Response(
                {"detail": "This attendance record does not require a reason."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ParentReasonUpdateSerializer(
            reason, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# AttendanceSummary ViewSet (read-only)
# ---------------------------------------------------------------------------

class AttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only analytics endpoint for attendance summaries.

    Filters:
      ?organization=<id>
      ?student=<id>
      ?academic_year=<id>

    Returns pre-computed totals and the attendance_rate percentage.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceSummarySerializer
    filter_backends = [SearchFilter]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__roll_no",
        "academic_year__name",
    ]

    def get_queryset(self):
        qs = AttendanceSummary.objects.select_related(
            "student", "academic_year", "organization"
        )
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("student"):
            qs = qs.filter(student_id=p["student"])
        if p.get("academic_year"):
            qs = qs.filter(academic_year_id=p["academic_year"])
        return qs
