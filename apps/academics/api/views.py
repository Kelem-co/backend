from academics.models import AcademicYear
from academics.models import CalendarDocument
from academics.models import Grade
from academics.models import GradeSubject
from academics.models import Section
from academics.models import Subject
from django.db import transaction
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.access import scope_queryset_for_user
from core.api.access import user_can_access_branch

from .serializers import AcademicYearSerializer
from .serializers import CalendarDocumentCurrentQuerySerializer
from .serializers import CalendarDocumentSerializer
from .serializers import CalendarDocumentUpsertSerializer
from .serializers import GradeSerializer
from .serializers import GradeSubjectReadSerializer
from .serializers import GradeSubjectSerializer
from .serializers import SectionSerializer
from .serializers import SubjectSerializer


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "branch__name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(self.queryset, self.request.user)


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(self.queryset, self.request.user)


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.select_related("grade", "branch", "academic_year").all()
    serializer_class = SectionSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "grade__name", "branch__name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(self.queryset, self.request.user)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.select_related("grade", "branch").all()
    serializer_class = SubjectSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "code", "grade__name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return scope_queryset_for_user(self.queryset, self.request.user)


class GradeSubjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for the grade-subject mapping.
    Supports filtering by ?grade=<id> and ?subject=<id> via query params,
    and text search via ?search=.
    """

    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["grade__name", "subject__name", "subject__code"]

    def get_queryset(self):
        qs = GradeSubject.objects.select_related("grade", "subject", "organization")
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_queryset_for_user(
            qs,
            self.request.user,
            branch_lookup="grade__branch",
        )
        grade_id = self.request.query_params.get("grade")
        subject_id = self.request.query_params.get("subject")
        organization_id = self.request.query_params.get("organization")
        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return GradeSubjectReadSerializer
        return GradeSubjectSerializer


CALENDAR_DOCUMENT_PARAMETERS = [
    OpenApiParameter(
        name="branch",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=True,
        description="Branch id for the current calendar document.",
    ),
    OpenApiParameter(
        name="organization",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=True,
        description="Organization id for the current calendar document.",
    ),
    OpenApiParameter(
        name="academic_year",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Optional academic year id for the current calendar document.",
    ),
]


class CalendarDocumentCurrentView(APIView):
    permission_classes = [IsAuthenticated]

    def _build_queryset(self):
        return scope_queryset_for_user(
            CalendarDocument.objects.select_related(
                "organization",
                "branch",
                "academic_year",
                "media_file",
            ),
            self.request.user,
        )

    @extend_schema(
        parameters=CALENDAR_DOCUMENT_PARAMETERS,
        responses={200: CalendarDocumentSerializer},
    )
    def get(self, request):
        serializer = CalendarDocumentCurrentQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        branch = serializer.validated_data["branch"]
        organization = serializer.validated_data["organization"]
        academic_year = serializer.validated_data.get("academic_year")

        queryset = self._build_queryset()
        filters = {
            "branch": branch,
            "organization": organization,
        }
        if academic_year is not None:
            filters["academic_year"] = academic_year
        else:
            filters["academic_year__isnull"] = True

        document = get_object_or_404(queryset, **filters)
        return Response(CalendarDocumentSerializer(document).data)

    @extend_schema(
        request=CalendarDocumentUpsertSerializer,
        responses={200: CalendarDocumentSerializer, 201: CalendarDocumentSerializer},
    )
    def post(self, request):
        serializer = CalendarDocumentUpsertSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        branch = serializer.validated_data["branch"]
        if not user_can_access_branch(request.user, branch):
            raise Http404

        academic_year = serializer.validated_data.get("academic_year")
        filters = {
            "organization": serializer.validated_data["organization"],
            "branch": branch,
            "academic_year": academic_year,
        }

        with transaction.atomic():
            document, created = (
                CalendarDocument.objects.select_for_update().get_or_create(
                    **filters,
                    defaults={"media_file": serializer.validated_data["media_file"]},
                )
            )
            if not created:
                document.media_file = serializer.validated_data["media_file"]
                document.save(update_fields=["media_file", "updated_at"])

        response_serializer = CalendarDocumentSerializer(document)
        response_status = 201 if created else 200
        return Response(response_serializer.data, status=response_status)
