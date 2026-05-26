from assessments.models import Assessment
from assessments.models import AssessmentResult
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.access import scope_assessment_result_queryset_for_user
from core.api.access import user_can_access_branch
from core.api.access import user_can_access_student_as_parent_or_staff
from core.api.access import user_resource_access_filter

from .serializers import AssessmentReadSerializer
from .serializers import AssessmentResultReadSerializer
from .serializers import AssessmentResultSerializer
from .serializers import AssessmentSerializer
from .serializers import BulkGradeSerializer
from .serializers import ParentHomeworkConfirmSerializer

# ---------------------------------------------------------------------------
# Assessment ViewSet
# ---------------------------------------------------------------------------


def scope_assessment_queryset_for_user(queryset, user):
    access_filter = user_resource_access_filter(user)
    if getattr(user, "is_authenticated", False):
        access_filter |= Q(teacher_assignment__teacher__user=user)
    return queryset.filter(access_filter).distinct()


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for Assessments (Assignments, Exams, Homework, Quizzes, etc.).

    Query-param filters:
      ?organization=<id>
      ?branch=<id>
      ?teacher_assignment=<id>
      ?teacher=<id>
      ?section=<id>
      ?subject=<id>
      ?task_type=ASSIGNMENT|EXAM|QUIZ|HOMEWORK|PROJECT|LAB
      ?status=DRAFT|PUBLISHED|CLOSED

    Text search (?search=):
      Title, description, section name, subject name, teacher name.

    Custom actions:
      GET  /assessments/by-section/?section=<id>
           All assessments for a given section (all subjects).

      GET  /assessments/by-teacher/?teacher=<id>
           All assessments created under a teacher's assignments.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "title",
        "description",
        "teacher_assignment__section__name",
        "teacher_assignment__subject__name",
        "teacher_assignment__teacher__user__name",
    ]

    def get_queryset(self):
        qs = Assessment.objects.select_related(
            "teacher_assignment__section__grade",
            "teacher_assignment__subject",
            "teacher_assignment__teacher__user",
            "teacher_assignment__academic_year",
            "branch",
            "organization",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        qs = scope_assessment_queryset_for_user(qs, self.request.user)
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("branch"):
            qs = qs.filter(branch_id=p["branch"])
        if p.get("teacher_assignment"):
            qs = qs.filter(teacher_assignment_id=p["teacher_assignment"])
        if p.get("teacher"):
            qs = qs.filter(teacher_assignment__teacher_id=p["teacher"])
        if p.get("section"):
            qs = qs.filter(teacher_assignment__section_id=p["section"])
        if p.get("subject"):
            qs = qs.filter(teacher_assignment__subject_id=p["subject"])
        if p.get("task_type"):
            qs = qs.filter(task_type=p["task_type"].upper())
        if p.get("status"):
            qs = qs.filter(status=p["status"].upper())
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "by_section", "by_teacher"]:
            return AssessmentReadSerializer
        return AssessmentSerializer

    # ------------------------------------------------------------------
    # GET /assessments/by-section/?section=<id>[&task_type=][&status=]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-section")
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="section",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter by section ID.",
                required=True,
            ),
        ],
    )
    def by_section(self, request):
        """All assessments for a given section across all subjects."""
        section_id = request.query_params.get("section")
        if not section_id:
            return Response(
                {"detail": "Query parameter 'section' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(teacher_assignment__section_id=section_id)
        qs = self.filter_queryset(qs)
        serializer = AssessmentReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /assessments/by-teacher/?teacher=<id>[&task_type=][&status=]
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-teacher")
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="teacher",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter by teacher ID.",
                required=True,
            ),
        ],
    )
    def by_teacher(self, request):
        """All assessments created by/for a specific teacher."""
        teacher_id = request.query_params.get("teacher")
        if not teacher_id:
            return Response(
                {"detail": "Query parameter 'teacher' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(teacher_assignment__teacher_id=teacher_id)
        qs = self.filter_queryset(qs)
        serializer = AssessmentReadSerializer(qs, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# AssessmentResult ViewSet
# ---------------------------------------------------------------------------


class AssessmentResultViewSet(viewsets.ModelViewSet):
    """
    CRUD for individual Assessment Results.

    Query-param filters:
      ?organization=<id>
      ?assessment=<id>
      ?student=<id>
      ?submission_status=PENDING|SUBMITTED|LATE|MISSING|GRADED
      ?parent_confirmed=true|false

    Text search (?search=):
      Student first/last name, roll number, assessment title.

    Custom actions:
      POST /assessment-results/bulk-grade/
           Teacher submits grades for a whole section in one request.

      PATCH /assessment-results/<id>/confirm-homework/
           Parent confirms their child completed the homework.

      GET  /assessment-results/by-assessment/?assessment=<id>
           All results for one assessment (full section overview).

      GET  /assessment-results/by-student/?student=<id>
           All results for one student across all assessments.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__roll_no",
        "assessment__title",
    ]

    def get_queryset(self):
        qs = AssessmentResult.objects.select_related(
            "assessment__teacher_assignment__section__grade",
            "assessment__teacher_assignment__subject",
            "assessment__teacher_assignment__teacher__user",
            "assessment__teacher_assignment__academic_year",
            "student",
            "graded_by",
            "organization",
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()

        if self.action == "confirm_homework":
            qs = qs.filter(
                user_resource_access_filter(
                    self.request.user,
                    branch_lookup="assessment__branch",
                )
                | Q(student__parent_links__parent__user=self.request.user),
            ).distinct()
        else:
            qs = scope_assessment_result_queryset_for_user(qs, self.request.user)
        p = self.request.query_params
        if p.get("organization"):
            qs = qs.filter(organization_id=p["organization"])
        if p.get("assessment"):
            qs = qs.filter(assessment_id=p["assessment"])
        if p.get("student"):
            qs = qs.filter(student_id=p["student"])
        if p.get("submission_status"):
            qs = qs.filter(submission_status=p["submission_status"].upper())
        if p.get("parent_confirmed") is not None:
            val = p["parent_confirmed"].lower() in ("true", "1", "yes")
            qs = qs.filter(parent_confirmed=val)
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "by_assessment", "by_student"]:
            return AssessmentResultReadSerializer
        if self.action == "confirm_homework":
            return ParentHomeworkConfirmSerializer
        return AssessmentResultSerializer

    def perform_create(self, serializer):
        self._enforce_teacher_result_access(
            serializer.validated_data["assessment"],
        )
        serializer.save(graded_by=self.request.user)

    def perform_update(self, serializer):
        assessment = serializer.validated_data.get(
            "assessment",
            serializer.instance.assessment,
        )
        self._enforce_teacher_result_access(assessment)
        serializer.save(graded_by=self.request.user)

    def _enforce_teacher_result_access(self, assessment):
        if user_can_access_branch(self.request.user, assessment.branch):
            return

        if assessment.teacher_assignment.teacher.user_id == self.request.user.id:
            return

        message = "You do not have permission to manage results for this assessment."
        raise PermissionDenied(message)

    # ------------------------------------------------------------------
    # POST /assessment-results/bulk-grade/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-grade")
    def bulk_grade(self, request):
        """
        Teacher posts grades for a whole section at once.

        Payload:
        {
          "assessment": "<uuid>",
          "results": [
            {"student": "<uuid>", "obtained_marks": 38, "submission_status": "GRADED"},
            {"student": "<uuid>", "submission_status": "MISSING"},
            ...
          ]
        }

        Idempotent: existing result rows are updated; new ones are created.
        The post_save signal fires for each saved result, triggering the
        low-grade intervention check in the analytics app.
        """
        serializer = BulkGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assessment = serializer.validated_data["assessment"]
        items = serializer.validated_data["results"]

        self._enforce_teacher_result_access(assessment)

        created_ids, updated_ids, errors = [], [], []

        with transaction.atomic():
            for item in items:
                try:
                    obj, was_created = AssessmentResult.objects.update_or_create(
                        assessment=assessment,
                        student=item["student"],
                        defaults={
                            "organization": assessment.organization,
                            "graded_by": request.user,
                            "obtained_marks": item.get("obtained_marks"),
                            "submission_status": item["submission_status"],
                            "feedback": item.get("feedback", ""),
                        },
                    )
                    if was_created:
                        created_ids.append(str(obj.id))
                    else:
                        updated_ids.append(str(obj.id))
                except IntegrityError as exc:
                    errors.append(
                        {"student": str(item["student"].id), "error": str(exc)},
                    )

        return Response(
            {
                "assessment": str(assessment.id),
                "created": len(created_ids),
                "updated": len(updated_ids),
                "errors": errors,
            },
            status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # PATCH /assessment-results/<id>/confirm-homework/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["patch"], url_path="confirm-homework")
    def confirm_homework(self, request, pk=None):
        """
        Parent endpoint to confirm their child completed a homework task.

        Validates that:
          - The assessment is of type HOMEWORK.
          - The confirmation hasn't already been set.

        TODO: Add a permission class to restrict this to the student's
              linked parents (check students.ParentStudentLink).
        """
        result = self.get_object()
        if not user_can_access_student_as_parent_or_staff(request.user, result.student):
            message = "You cannot confirm this homework result."
            raise PermissionDenied(message)

        if result.parent_confirmed:
            return Response(
                {"detail": "Homework completion is already confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ParentHomeworkConfirmSerializer(
            result,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /assessment-results/by-assessment/?assessment=<id>
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-assessment")
    def by_assessment(self, request):
        """
        Full result list for one assessment — gives the teacher a
        section-level grade overview.
        """
        assessment_id = request.query_params.get("assessment")
        if not assessment_id:
            return Response(
                {"detail": "Query parameter 'assessment' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(assessment_id=assessment_id)
        qs = self.filter_queryset(qs)
        serializer = AssessmentResultReadSerializer(qs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /assessment-results/by-student/?student=<id>
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="by-student")
    def by_student(self, request):
        """
        Full assessment history for one student — useful for parent / student
        portal views.
        Optional: ?assessment__task_type=HOMEWORK to filter by type.
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response(
                {"detail": "Query parameter 'student' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(student_id=student_id)
        task_type = request.query_params.get("task_type")
        if task_type:
            qs = qs.filter(assessment__task_type=task_type.upper())
        qs = self.filter_queryset(qs)
        serializer = AssessmentResultReadSerializer(qs, many=True)
        return Response(serializer.data)
