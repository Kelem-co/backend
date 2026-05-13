from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from academics.models import AcademicYear, Grade, Section, Subject, GradeSubject
from .serializers import (
    AcademicYearSerializer,
    GradeSerializer,
    SectionSerializer,
    SubjectSerializer,
    GradeSubjectSerializer,
    GradeSubjectReadSerializer,
)


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "branch__name"]


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name"]


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.select_related("grade", "branch", "academic_year").all()
    serializer_class = SectionSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "grade__name", "branch__name"]


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.select_related("grade", "branch").all()
    serializer_class = SubjectSerializer
    lookup_field = "id"
    filter_backends = [SearchFilter]
    search_fields = ["name", "code", "grade__name"]


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
        qs = GradeSubject.objects.select_related(
            "grade", "subject", "organization"
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
