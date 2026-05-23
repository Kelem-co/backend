from branches.models import Branch
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from teachers.models import HomeroomAssignment
from teachers.models import Teacher
from teachers.models import TeacherQualification
from teachers.models import TeacherSubjectAssignment

from core.api.access import scope_queryset_for_user
from core.api.access import user_can_access_branch
from core.models import ImportJob
from core.tasks import process_bulk_import

from .serializers import BulkImportSerializer
from .serializers import HomeroomAssignmentReadSerializer
from .serializers import HomeroomAssignmentSerializer
from .serializers import SectionTeacherScheduleSerializer
from .serializers import TeacherQualificationSerializer
from .serializers import TeacherSerializer
from .serializers import TeacherSubjectAssignmentReadSerializer
from .serializers import TeacherSubjectAssignmentSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    """
    CRUD for Teacher profiles.

    Search: ?search=<name|employee_id|specialization>
    Filter: ?organization=<id>, ?branch=<id>

    Custom actions:
      GET /teachers/<id>/qualifications/  - list qualifications for a teacher
      GET /teachers/<id>/assignments/     - list subject assignments for a teacher
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = [
        "user__name",
        "user__email",
        "employee_id",
        "specialization",
    ]

    def get_queryset(self):
        qs = Teacher.objects.select_related(
            "user",
            "branch",
            "organization",
        ).prefetch_related(
            Prefetch(
                "qualifications",
                queryset=TeacherQualification.objects.select_related(
                    "certificate_copy",
                    "organization",
                ),
            ),
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(qs, self.request.user)
        org = self.request.query_params.get("organization")
        branch = self.request.query_params.get("branch")
        if org:
            qs = qs.filter(organization_id=org)
        if branch:
            qs = qs.filter(branch_id=branch)
        return qs

    def get_serializer_class(self):
        if self.action == "bulk_import":
            return BulkImportSerializer
        return TeacherSerializer

    # ------------------------------------------------------------------
    # POST /teachers/bulk-import/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        """Bulk import teachers from CSV/Excel."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data["organization"]
        branch_id = serializer.validated_data["branch"]
        media_file = serializer.validated_data["file"]

        # Permission check: Check if user has access to this branch
        try:
            branch = Branch.objects.select_related("organization").get(
                id=branch_id,
                organization_id=organization_id,
            )
        except Branch.DoesNotExist:
            return Response(
                {"detail": "Branch not found or does not belong to organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_can_access_branch(request.user, branch):
            return Response(
                {"detail": "You do not have permission to import to this branch."},
                status=status.HTTP_403_FORBIDDEN,
            )

        import_job = ImportJob.objects.create(
            file=media_file,
            module="teachers",
            organization_id=organization_id,
            branch_id=branch_id,
            created_by=request.user,
        )

        process_bulk_import.delay(str(import_job.id))

        return Response(
            {"task_id": str(import_job.id), "detail": "Bulk import process started."},
            status=status.HTTP_202_ACCEPTED,
        )

    # ------------------------------------------------------------------
    # /teachers/<id>/qualifications/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="qualifications")
    def qualifications(self, request, pk=None):
        """Return all qualifications for this teacher."""
        teacher = self.get_object()
        qs = teacher.qualifications.select_related("certificate_copy", "organization")
        serializer = TeacherQualificationSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # /teachers/<id>/assignments/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="assignments")
    def assignments(self, request, pk=None):
        """Return all subject assignments for this teacher."""
        teacher = self.get_object()
        qs = teacher.subject_assignments.select_related(
            "subject",
            "section",
            "academic_year",
        ).all()
        serializer = TeacherSubjectAssignmentReadSerializer(qs, many=True)
        return Response(serializer.data)


class TeacherQualificationViewSet(viewsets.ModelViewSet):
    """
    CRUD for TeacherQualification.

    Filter: ?teacher=<id>, ?organization=<id>
    Search: ?search=<degree_name|institution|field_of_study>
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["degree_name", "institution", "field_of_study"]

    def get_queryset(self):
        qs = TeacherQualification.objects.select_related(
            "teacher__user",
            "organization",
            "certificate_copy",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(
            qs,
            self.request.user,
            branch_lookup="teacher__branch",
        )
        teacher_id = self.request.query_params.get("teacher")
        org = self.request.query_params.get("organization")
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
        if org:
            qs = qs.filter(organization_id=org)
        return qs

    def get_serializer_class(self):
        return TeacherQualificationSerializer


class TeacherSubjectAssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for TeacherSubjectAssignment (the junction table).

    Filter: ?teacher, ?subject, ?section, ?academic_year, ?organization
    Search: ?search=<teacher_name|subject|section>

    Custom actions:
      GET /teacher-assignments/by-section/?section=<id>
          Returns every subject taught in that section and who teaches it.
      GET /teacher-assignments/by-subject/?subject=<id>&academic_year=<id>
          Returns every teacher assigned to a subject for a given year.
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = [
        "teacher__user__name",
        "teacher__employee_id",
        "subject__name",
        "section__name",
    ]

    def get_queryset(self):
        qs = TeacherSubjectAssignment.objects.select_related(
            "teacher__user",
            "teacher__branch",
            "subject",
            "subject__grade",
            "section",
            "academic_year",
            "organization",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(
            qs,
            self.request.user,
            branch_lookup="section__branch",
        )
        filters = {}
        for param in ("teacher", "subject", "section", "academic_year", "organization"):
            val = self.request.query_params.get(param)
            if val:
                filters[f"{param}_id"] = val
        return qs.filter(**filters)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "by_section", "by_subject"]:
            return TeacherSubjectAssignmentReadSerializer
        return TeacherSubjectAssignmentSerializer

    # ------------------------------------------------------------------
    # GET /teacher-assignments/by-section/?section=<id>
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
    def by_section(self, request):
        """
        Given a section id, return all subjects taught in that section
        together with the teacher responsible for each.

        Required query param: ?section=<uuid>
        Optional: ?academic_year=<uuid>
        """
        section_id = request.query_params.get("section")
        if not section_id:
            return Response(
                {"detail": "Query parameter 'section' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(section_id=section_id)
        academic_year_id = request.query_params.get("academic_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)

        serializer = SectionTeacherScheduleSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /teacher-assignments/by-subject/?subject=<id>&academic_year=<id>
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-subject")
    def by_subject(self, request):
        """
        Given a subject id, return all teachers assigned to it (optionally
        filter by academic year).

        Required query param: ?subject=<uuid>
        Optional: ?academic_year=<uuid>
        """
        subject_id = request.query_params.get("subject")
        if not subject_id:
            return Response(
                {"detail": "Query parameter 'subject' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(subject_id=subject_id)
        academic_year_id = request.query_params.get("academic_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)

        serializer = TeacherSubjectAssignmentReadSerializer(qs, many=True)
        return Response(serializer.data)


class HomeroomAssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for homeroom teacher assignments.

    Each section may have **at most one** homeroom teacher per academic year
    (enforced by the model's unique_together constraint).

    Filters (query params):
      ?organization=<id>
      ?branch=<id>
      ?academic_year=<id>
      ?section=<id>
      ?teacher=<id>

    Text search (?search=):
      - Teacher name
      - Teacher employee ID
      - Teacher email
      - Section name
      - Grade name
      - Academic year name

    Custom actions:
      GET /homeroom-assignments/by-section/?section=<id>
          Returns the homeroom teacher (with full details) for a section.
          Optionally filter by ?academic_year=<id>.

      GET /homeroom-assignments/by-teacher/?teacher=<id>
          Returns all sections this teacher is homeroom for.
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = [
        "teacher__user__name",
        "teacher__user__email",
        "teacher__employee_id",
        "section__name",
        "section__grade__name",
        "academic_year__name",
        "branch__name",
    ]

    def get_queryset(self):
        qs = HomeroomAssignment.objects.select_related(
            "teacher__user",
            "teacher__branch",
            "section__grade",
            "academic_year",
            "branch",
            "organization",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(qs, self.request.user)
        filters = {}
        for param in ("organization", "branch", "academic_year", "section", "teacher"):
            val = self.request.query_params.get(param)
            if val:
                filters[f"{param}_id"] = val
        return qs.filter(**filters)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "by_section", "by_teacher"]:
            return HomeroomAssignmentReadSerializer
        return HomeroomAssignmentSerializer

    # ------------------------------------------------------------------
    # GET /homeroom-assignments/by-section/?section=<id>[&academic_year=<id>]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
    def by_section(self, request):
        """
        Return the homeroom teacher assignment for a given section.
        If ?academic_year is omitted, returns all years (useful for history).
        """
        section_id = request.query_params.get("section")
        if not section_id:
            return Response(
                {"detail": "Query parameter 'section' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(section_id=section_id)

        academic_year_id = request.query_params.get("academic_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)

        serializer = HomeroomAssignmentReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /homeroom-assignments/by-teacher/?teacher=<id>[&academic_year=<id>]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-teacher")
    def by_teacher(self, request):
        """
        Return all sections a given teacher is homeroom for.
        Optionally filter by ?academic_year.
        """
        teacher_id = request.query_params.get("teacher")
        if not teacher_id:
            return Response(
                {"detail": "Query parameter 'teacher' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(teacher_id=teacher_id)

        academic_year_id = request.query_params.get("academic_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)

        serializer = HomeroomAssignmentReadSerializer(qs, many=True)
        return Response(serializer.data)
