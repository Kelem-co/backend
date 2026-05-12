from rest_framework import viewsets
from academics.models import AcademicYear, Grade, Section, Subject
from .serializers import (
    AcademicYearSerializer,
    GradeSerializer,
    SectionSerializer,
    SubjectSerializer,
)

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    lookup_field = "id"

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    lookup_field = "id"

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    lookup_field = "id"

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    lookup_field = "id"
