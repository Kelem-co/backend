from academics.models import AcademicYear
from academics.models import Grade
from academics.models import GradeSubject
from academics.models import Section
from academics.models import Subject
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from core.api.access import scope_queryset_for_user

from .serializers import AcademicYearSerializer
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
