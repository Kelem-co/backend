from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from students.models import Student, ParentStudentLink
from .serializers import (
    StudentSerializer,
    StudentReadSerializer,
    ParentStudentLinkSerializer,
    ParentStudentLinkReadSerializer,
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
        )
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
        if self.action in ["list", "retrieve", "by_section", "by_grade"]:
            return StudentReadSerializer
        return StudentSerializer

    # ------------------------------------------------------------------
    # GET /students/by-section/?section=<id>[&status=][&academic_year=]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
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


class ParentStudentLinkViewSet(viewsets.ModelViewSet):
    """
    CRUD for parent-student relationships.
    Read responses include full student and parent details.
    """

    queryset = ParentStudentLink.objects.select_related(
        "student__current_section__grade",
        "student__current_section__academic_year",
        "student__branch",
        "parent",
    ).all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ParentStudentLinkReadSerializer
        return ParentStudentLinkSerializer
