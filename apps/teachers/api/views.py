import secrets

from branches.models import Branch
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from drf_spectacular.utils import inline_serializer
from rest_framework import status
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from teachers.models import HomeroomAssignment
from teachers.models import Teacher
from teachers.models import TeacherQualification
from teachers.models import TeacherSubjectAssignment

from accounts.email import TeacherInvitationEmail
from accounts.models import User
from core.api.access import user_resource_access_filter
from core.api.access import user_can_access_branch
from core.models import ImportJob
from core.tasks import process_bulk_import

from .serializers import BulkImportSerializer
from .serializers import HomeroomAssignmentReadSerializer
from .serializers import HomeroomAssignmentSerializer
from .serializers import SectionTeacherScheduleSerializer
from .serializers import TeacherCompleteInvitationSerializer
from .serializers import TeacherInviteSerializer
from .serializers import TeacherQualificationSerializer
from .serializers import TeacherSectionSerializer
from .serializers import TeacherSerializer
from .serializers import TeacherSubjectAssignmentReadSerializer
from .serializers import TeacherSubjectAssignmentSerializer


TEACHER_LIST_PARAMETERS = [
    OpenApiParameter(
        name="organization",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter teachers by organization ID.",
        required=False,
    ),
    OpenApiParameter(
        name="branch",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter teachers by branch ID.",
        required=False,
    ),
    OpenApiParameter(
        name="user",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter teachers by related user ID.",
        required=False,
    ),
]


def scope_teacher_queryset_for_user(
    queryset,
    user,
    *,
    own_lookup: str,
    organization_lookup: str = "organization",
    branch_lookup: str | None = "branch",
):
    """
    Extend the shared access rules so teachers can access their own records.
    """
    access_filter = user_resource_access_filter(
        user,
        organization_lookup=organization_lookup,
        branch_lookup=branch_lookup,
    )
    if getattr(user, "is_authenticated", False):
        access_filter |= Q(**{own_lookup: user})
    return queryset.filter(access_filter).distinct()


@extend_schema_view(
    list=extend_schema(parameters=TEACHER_LIST_PARAMETERS),
)
class TeacherViewSet(viewsets.ModelViewSet):
    """
    CRUD for Teacher profiles.

    Search: ?search=<name|employee_id|specialization>
    Filter: ?organization=<id>, ?branch=<id>, ?user=<id>

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

        qs = scope_teacher_queryset_for_user(
            qs,
            self.request.user,
            own_lookup="user",
        )
        org = self.request.query_params.get("organization")
        branch = self.request.query_params.get("branch")
        user_id = self.request.query_params.get("user")
        if org:
            qs = qs.filter(organization_id=org)
        if branch:
            qs = qs.filter(branch_id=branch)
        if user_id:
            qs = qs.filter(user_id=user_id)
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
    def qualifications(self, request, *args, **kwargs):
        """Return all qualifications for this teacher."""
        teacher = self.get_object()
        qs = teacher.qualifications.select_related("certificate_copy", "organization")
        serializer = TeacherQualificationSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # /teachers/<id>/assignments/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="assignments")
    def assignments(self, request, *args, **kwargs):
        """Return all subject assignments for this teacher."""
        teacher = self.get_object()
        qs = teacher.subject_assignments.select_related(
            "subject",
            "section",
            "academic_year",
        ).all()
        serializer = TeacherSubjectAssignmentReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # /teachers/<id>/sections/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="sections")
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="academic_year",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Optionally filter sections by academic year ID.",
                required=False,
            ),
        ],
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="TeacherSectionsResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "sections": TeacherSectionSerializer(many=True),
                },
            ),
        },
    )
    def sections(self, request, *args, **kwargs):
        """
        Return the unique sections (with grade and academic year context)
        that this teacher is assigned to teach.

        Each entry lists the subjects the teacher covers in that section
        so the caller never needs a follow-up request.

        Optional query param:
          ?academic_year=<uuid>  — narrow to a specific academic year.
        """
        teacher = self.get_object()
        qs = teacher.subject_assignments.select_related(
            "subject__grade",
            "section",
            "academic_year",
        )

        academic_year_id = request.query_params.get("academic_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)

        # Build a deduplicated map keyed by (section_id, academic_year_id)
        # so each section appears once even when the teacher covers multiple
        # subjects there.
        section_map: dict[tuple, dict] = {}
        for assignment in qs:
            key = (str(assignment.section_id), str(assignment.academic_year_id))
            if key not in section_map:
                section_map[key] = {
                    "section_id": assignment.section_id,
                    "section_name": assignment.section.name,
                    "grade_id": assignment.section.grade_id,
                    "grade_name": assignment.section.grade.name,
                    "grade_level": assignment.section.grade.level,
                    "academic_year_id": assignment.academic_year_id,
                    "academic_year_name": assignment.academic_year.name,
                    "subjects": [],
                }
            section_map[key]["subjects"].append(
                {
                    "subject_id": str(assignment.subject_id),
                    "subject_name": assignment.subject.name,
                    "subject_code": assignment.subject.code,
                },
            )

        # Sort by grade level then section name for a predictable order
        result = sorted(
            section_map.values(),
            key=lambda x: (x["grade_level"], x["section_name"]),
        )
        serializer = TeacherSectionSerializer(result, many=True)
        return Response({"count": len(result), "sections": serializer.data})


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

        qs = scope_teacher_queryset_for_user(
            qs,
            self.request.user,
            own_lookup="teacher__user",
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

        qs = scope_teacher_queryset_for_user(
            qs,
            self.request.user,
            own_lookup="teacher__user",
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

        qs = scope_teacher_queryset_for_user(
            qs,
            self.request.user,
            own_lookup="teacher__user",
        )
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


# ---------------------------------------------------------------------------
# Teacher invitation views
# ---------------------------------------------------------------------------


@extend_schema(request=TeacherInviteSerializer)
class TeacherInviteView(APIView):
    """
    Invite a new teacher by email.

    Creates an inactive User account with role=TEACHER, creates the
    Teacher profile, and sends an invitation email containing a
    password-set link.

    The link points to:
        {FRONTEND_DOMAIN}/complete-teacher-invitation/{uid}/{token}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TeacherInviteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        branch: Branch = data["branch"]

        # Create the user account (inactive until invitation is completed)
        random_password = secrets.token_urlsafe(16)
        user = User.objects.create_user(
            email=data["email"],
            password=random_password,
            name=data["name"],
            father_name=data["father_name"],
            grandfather_name=data["grandfather_name"],
            role=User.Role.TEACHER,
            is_active=False,
        )

        # Create the teacher profile linked to the branch
        Teacher.objects.create(
            user=user,
            organization=branch.organization,
            branch=branch,
            specialization=data.get("specialization", ""),
        )

        # Build the invitation link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = f"complete-teacher-invitation/{uid}/{token}"

        email_obj = TeacherInvitationEmail(
            request,
            context={
                "user": user,
                "branch_name": branch.name,
                "invited_by": request.user.name,
                "url": path,
            },
        )
        email_obj.send([user.email])

        return Response(
            {"message": "Teacher invitation sent successfully."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=TeacherCompleteInvitationSerializer)
class TeacherCompleteInvitationView(APIView):
    """
    Complete a teacher invitation by setting a password.

    No authentication required — the uid/token pair from the email
    acts as the credential.

    On success the user account is activated, verified_at is stamped,
    and the Teacher profile status is left as-is (teachers have no
    INACTIVE/ACTIVE status field — the User.is_active flag is the gate).
    """

    permission_classes = []

    def post(self, request):
        serializer = TeacherCompleteInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        # Decode the user
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as err:
            raise ValidationError({"uid": "Invalid user ID."}) from err

        # Guard: must be a pending teacher invitation
        if user.role != User.Role.TEACHER or user.is_active:
            raise ValidationError({"uid": "Invalid or expired invitation."})

        # Verify the token
        if not default_token_generator.check_token(user, token):
            raise ValidationError({"token": "Invalid or expired token."})

        # Ensure a teacher profile actually exists for this user
        if not Teacher.objects.filter(user=user).exists():
            raise ValidationError({"uid": "Invalid or expired invitation."})

        # Activate the account
        user.set_password(new_password)
        user.is_active = True
        user.verified_at = timezone.now()
        user.save()

        return Response(
            {"message": "Password set and account activated successfully."},
            status=status.HTTP_200_OK,
        )
