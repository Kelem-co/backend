from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import OpenApiTypes
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from students.models import Parent
from students.models import ParentStudentLink
from students.models import Student
from branches.models import Branch

from core.api.access import scope_queryset_for_user
from core.api.access import user_can_access_parent
from core.api.access import user_can_access_branch
from core.models import ImportJob
from core.tasks import process_bulk_import

from .serializers import BulkImportSerializer
from .serializers import ParentReadSerializer
from .serializers import ParentSerializer
from .serializers import ParentStudentLinkReadSerializer
from .serializers import ParentStudentLinkSerializer
from .serializers import StudentReadSerializer
from .serializers import StudentSerializer

STUDENT_LIST_PARAMETERS = [
    OpenApiParameter(
        name="section",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by current section id.",
    ),
    OpenApiParameter(
        name="grade",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by grade id.",
    ),
    OpenApiParameter(
        name="branch",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by branch id.",
    ),
    OpenApiParameter(
        name="organization",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by organization id.",
    ),
    OpenApiParameter(
        name="academic_year",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by academic year id.",
    ),
    OpenApiParameter(
        name="status",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=[choice for choice, _label in Student.Status.choices],
        description="Filter by student status.",
    ),
    OpenApiParameter(
        name="gender",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=[choice for choice, _label in Student.Gender.choices],
        description="Filter by student gender.",
    ),
]

STUDENT_BY_SECTION_PARAMETERS = [
    OpenApiParameter(
        name="section",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Section id to list students from.",
        required=True,
    ),
    *[
        parameter
        for parameter in STUDENT_LIST_PARAMETERS
        if parameter.name not in {"section", "grade"}
    ],
]

STUDENT_BY_GRADE_PARAMETERS = [
    OpenApiParameter(
        name="grade",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Grade id to list students from.",
        required=True,
    ),
    *[
        parameter
        for parameter in STUDENT_LIST_PARAMETERS
        if parameter.name not in {"section", "grade"}
    ],
    OpenApiParameter(
        name="section",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Optional section id within the selected grade.",
    ),
]

PARENT_LIST_PARAMETERS = [
    OpenApiParameter(
        name="organization",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by parent organization id.",
    ),
    OpenApiParameter(
        name="branch",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by parent branch id.",
    ),
    OpenApiParameter(
        name="user",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Filter by linked user id.",
    ),
    OpenApiParameter(
        name="occupation",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Filter by occupation.",
    ),
    OpenApiParameter(
        name="is_active",
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description="Filter by active parent profiles.",
    ),
]

PARENT_BY_BRANCH_PARAMETERS = [
    OpenApiParameter(
        name="branch",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Branch id to list parents from.",
        required=True,
    ),
]

PARENT_BY_ORGANIZATION_PARAMETERS = [
    OpenApiParameter(
        name="organization",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        description="Organization id to list parents from.",
        required=True,
    ),
]


@extend_schema_view(
    list=extend_schema(parameters=STUDENT_LIST_PARAMETERS),
    by_section=extend_schema(parameters=STUDENT_BY_SECTION_PARAMETERS),
    by_grade=extend_schema(parameters=STUDENT_BY_GRADE_PARAMETERS),
)
class StudentViewSet(viewsets.ModelViewSet):
    """
    CRUD for Students.

    Read responses automatically expand section, grade, branch, and
    academic-year details — no separate lookups needed.

    Query-param filters:
      ?section=<id>          Filter by current_section
      ?grade=<id>            Filter by section's grade
      ?branch=<id>           Filter by branch
      ?organization=<id>     Tenant filter
      ?academic_year=<id>    Filter by the academic year on the section
      ?status=ACTIVE|INACTIVE|WITHDRAWN|GRADUATED
      ?gender=MALE|FEMALE|OTHER

    Text search (?search=):
      Student first name, last name, roll number, section name, grade name

    Custom actions:
      GET /students/by-section/?section=<id>
          All students in a specific section with full details.

      GET /students/by-grade/?grade=<id>
          All students across every section of a grade with full details.
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = [
        "first_name",
        "last_name",
        "roll_no",
        "current_section__name",
        "current_section__grade__name",
    ]

    def get_queryset(self):
        qs = Student.objects.select_related(
            "current_section__grade",
            "current_section__academic_year",
            "branch",
            "organization",
            "photo",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(qs, self.request.user)
        params = self.request.query_params
        if params.get("section"):
            qs = qs.filter(current_section_id=params["section"])
        if params.get("grade"):
            qs = qs.filter(current_section__grade_id=params["grade"])
        if params.get("branch"):
            qs = qs.filter(branch_id=params["branch"])
        if params.get("organization"):
            qs = qs.filter(organization_id=params["organization"])
        if params.get("academic_year"):
            qs = qs.filter(current_section__academic_year_id=params["academic_year"])
        if params.get("status"):
            qs = qs.filter(status=params["status"].upper())
        if params.get("gender"):
            qs = qs.filter(gender=params["gender"].upper())
        return qs

    def get_serializer_class(self):
        if self.action == "bulk_import":
            return BulkImportSerializer
        if self.action in ["list", "retrieve", "by_section", "by_grade"]:
            return StudentReadSerializer
        return StudentSerializer

    # ------------------------------------------------------------------
    # POST /students/bulk-import/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        """Bulk import students from CSV/Excel."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data["organization"]
        branch_id = serializer.validated_data["branch"]
        uploaded_file = serializer.validated_data["file"]

        # Permission check
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
            file=uploaded_file,
            module="students",
            organization_id=organization_id,
            branch_id=branch_id,
            created_by=request.user
        )

        process_bulk_import.delay(str(import_job.id))

        return Response(
            {"task_id": str(import_job.id), "detail": "Bulk import process started."},
            status=status.HTTP_202_ACCEPTED,
        )


    # ------------------------------------------------------------------
    # GET /students/by-section/?section=<id>[&status=][&academic_year=]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
    @extend_schema(
        parameters=STUDENT_BY_SECTION_PARAMETERS,
    )
    def by_section(self, request):
        """
        Return all students in the given section with full details.
        Required: ?section=<uuid>
        Optional: ?status=ACTIVE, ?academic_year=<uuid>
        """
        section_id = request.query_params.get("section")
        if not section_id:
            return Response(
                {"detail": "Query parameter 'section' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(current_section_id=section_id)
        qs = self.filter_queryset(qs)
        serializer = StudentReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /students/by-grade/?grade=<id>[&status=][&section=]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-grade")
    @extend_schema(
        parameters=STUDENT_BY_GRADE_PARAMETERS,
    )
    def by_grade(self, request):
        """
        Return all students across all sections of a given grade.
        Required: ?grade=<uuid>
        Optional: ?section=<uuid>, ?status=ACTIVE, ?academic_year=<uuid>
        """
        grade_id = request.query_params.get("grade")
        if not grade_id:
            return Response(
                {"detail": "Query parameter 'grade' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(current_section__grade_id=grade_id)
        qs = self.filter_queryset(qs)
        serializer = StudentReadSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(parameters=PARENT_LIST_PARAMETERS),
    by_branch=extend_schema(parameters=PARENT_BY_BRANCH_PARAMETERS),
    by_organization=extend_schema(parameters=PARENT_BY_ORGANIZATION_PARAMETERS),
)
class ParentViewSet(viewsets.ModelViewSet):
    """CRUD for parent profiles and related branch/organization lookups."""

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "user__name",
        "user__email",
        "user__phone_number",
        "secondary_phone_number",
        "occupation",
        "work_address",
    ]

    def get_queryset(self):
        qs = Parent.objects.select_related("user").prefetch_related(
            "organizations",
            "branches",
            "student_links__student",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(
            qs,
            self.request.user,
            organization_lookup="organizations",
            branch_lookup="branches",
        )
        params = self.request.query_params
        if params.get("organization"):
            qs = qs.filter(organizations__id=params["organization"])
        if params.get("branch"):
            qs = qs.filter(branches__id=params["branch"])
        if params.get("user"):
            qs = qs.filter(user_id=params["user"])
        if params.get("occupation"):
            qs = qs.filter(occupation__iexact=params["occupation"])
        if params.get("is_active") is not None:
            is_active = params["is_active"].lower() in ("true", "1", "yes")
            qs = qs.filter(is_active=is_active)
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "bulk_import":
            return BulkImportSerializer
        if self.action in [
            "list",
            "retrieve",
            "by_branch",
            "by_organization",
            "branches",
            "organizations",
            "students",
            "me",
            "my_students",
        ]:
            return ParentReadSerializer
        return ParentSerializer

    # ------------------------------------------------------------------
    # POST /parents/bulk-import/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        """Bulk import parents from CSV/Excel."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data["organization"]
        branch_id = serializer.validated_data["branch"]
        uploaded_file = serializer.validated_data["file"]

        # Permission check
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
            file=uploaded_file,
            module="parents",
            organization_id=organization_id,
            branch_id=branch_id,
            created_by=request.user
        )

        process_bulk_import.delay(str(import_job.id))

        return Response(
            {"task_id": str(import_job.id), "detail": "Bulk import process started."},
            status=status.HTTP_202_ACCEPTED,
        )


    @action(detail=False, methods=["get"], url_path="by-branch")
    @extend_schema(parameters=PARENT_BY_BRANCH_PARAMETERS)
    def by_branch(self, request):
        branch_id = request.query_params.get("branch")
        if not branch_id:
            return Response(
                {"detail": "Query parameter 'branch' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.filter_queryset(self.get_queryset().filter(branches__id=branch_id))
        serializer = ParentReadSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-organization")
    @extend_schema(parameters=PARENT_BY_ORGANIZATION_PARAMETERS)
    def by_organization(self, request):
        organization_id = request.query_params.get("organization")
        if not organization_id:
            return Response(
                {"detail": "Query parameter 'organization' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.filter_queryset(
            self.get_queryset().filter(organizations__id=organization_id),
        )
        serializer = ParentReadSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="branches")
    def branches(self, request, **kwargs):
        parent = self.get_object()
        return Response(
            ParentReadSerializer(parent, context={"request": request}).data[
                "branch_details"
            ],
        )

    @action(detail=True, methods=["get"], url_path="organizations")
    def organizations(self, request, **kwargs):
        parent = self.get_object()
        return Response(
            ParentReadSerializer(parent, context={"request": request}).data[
                "organization_details"
            ],
        )

    @action(detail=True, methods=["get"], url_path="students")
    def students(self, request, **kwargs):
        parent = self.get_object()
        return Response(
            ParentReadSerializer(parent, context={"request": request}).data[
                "student_details"
            ],
        )

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        try:
            parent = request.user.parent_profile
        except Parent.DoesNotExist:
            return Response(
                {"detail": "No parent profile found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user_can_access_parent(request.user, parent):
            return Response(
                {"detail": "You do not have access to this parent profile."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(ParentReadSerializer(parent).data)

    @action(detail=False, methods=["get"], url_path="my-students")
    def my_students(self, request):
        try:
            parent = request.user.parent_profile
        except Parent.DoesNotExist:
            return Response(
                {"detail": "No parent profile found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = [
            link.student
            for link in parent.student_links.select_related(
                "student__current_section__grade",
                "student__current_section__academic_year",
                "student__branch",
                "student__organization",
            )
        ]
        return Response(StudentReadSerializer(students, many=True).data)


class ParentStudentLinkViewSet(viewsets.ModelViewSet):
    """
    CRUD for parent-student relationships.
    Read responses include full student and parent details.
    """

    queryset = (
        ParentStudentLink.objects.select_related(
            "student__current_section__grade",
            "student__current_section__academic_year",
            "student__branch",
            "parent__user",
        )
        .prefetch_related(
            "parent__organizations",
            "parent__branches",
        )
        .all()
    )
    lookup_field = "id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(
            self.queryset,
            self.request.user,
            organization_lookup="parent__organizations",
            branch_lookup="parent__branches",
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ParentStudentLinkReadSerializer
        return ParentStudentLinkSerializer
