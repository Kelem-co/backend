from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from assessments.models import Assessment, AssessmentResult


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------

ASSESSMENT_BASE_FIELDS = [
    "id",
    "organization",
    "branch",
    "teacher_assignment",
    "title",
    "task_type",
    "description",
    "total_marks",
    "passing_marks",
    "due_date",
    "status",
    "created_at",
    "updated_at",
]


class AssessmentSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids."""

    class Meta:
        model = Assessment
        fields = ASSESSMENT_BASE_FIELDS
        read_only_fields = ["id", "created_at", "updated_at"]


class AssessmentReadSerializer(AssessmentSerializer):
    """Read serializer — expands all related context."""

    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Derived from teacher_assignment
    section_name = serializers.CharField(source="teacher_assignment.section.name", read_only=True)
    grade_name = serializers.CharField(source="teacher_assignment.section.grade.name", read_only=True)
    subject_name = serializers.CharField(source="teacher_assignment.subject.name", read_only=True)
    subject_code = serializers.CharField(source="teacher_assignment.subject.code", read_only=True)
    teacher_name = serializers.CharField(source="teacher_assignment.teacher.user.name", read_only=True)
    teacher_employee_id = serializers.CharField(source="teacher_assignment.teacher.employee_id", read_only=True)
    academic_year_name = serializers.CharField(source="teacher_assignment.academic_year.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    result_count = serializers.SerializerMethodField()

    class Meta(AssessmentSerializer.Meta):
        fields = ASSESSMENT_BASE_FIELDS + [
            "task_type_display",
            "status_display",
            "section_name",
            "grade_name",
            "subject_name",
            "subject_code",
            "teacher_name",
            "teacher_employee_id",
            "academic_year_name",
            "branch_name",
            "result_count",
        ]

    def get_result_count(self, obj):
        return obj.results.count()


# ---------------------------------------------------------------------------
# AssessmentResult — single record
# ---------------------------------------------------------------------------

RESULT_BASE_FIELDS = [
    "id",
    "organization",
    "assessment",
    "student",
    "graded_by",
    "obtained_marks",
    "submission_status",
    "feedback",
    "parent_confirmed",
    "parent_confirmed_by",
    "parent_confirmed_at",
    "created_at",
    "updated_at",
]


class AssessmentResultSerializer(serializers.ModelSerializer):
    """Write serializer."""

    class Meta:
        model = AssessmentResult
        fields = RESULT_BASE_FIELDS
        read_only_fields = [
            "id", "graded_by", "parent_confirmed_by",
            "parent_confirmed_at", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        assessment = attrs.get("assessment", getattr(self.instance, "assessment", None))
        obtained = attrs.get("obtained_marks", getattr(self.instance, "obtained_marks", None))
        if assessment and obtained is not None:
            if obtained > assessment.total_marks:
                raise ValidationError(
                    {"obtained_marks": "Obtained marks cannot exceed total marks."}
                )
        return attrs


class AssessmentResultReadSerializer(AssessmentResultSerializer):
    """Read serializer with expanded details."""

    submission_status_display = serializers.CharField(
        source="get_submission_status_display", read_only=True
    )
    student_name = serializers.SerializerMethodField()
    student_roll_no = serializers.CharField(source="student.roll_no", read_only=True)
    section_name = serializers.CharField(
        source="assessment.teacher_assignment.section.name", read_only=True
    )
    subject_name = serializers.CharField(
        source="assessment.teacher_assignment.subject.name", read_only=True
    )
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    total_marks = serializers.DecimalField(
        source="assessment.total_marks", max_digits=6, decimal_places=2, read_only=True
    )
    passing_marks = serializers.DecimalField(
        source="assessment.passing_marks", max_digits=6, decimal_places=2, read_only=True
    )
    percentage = serializers.FloatField(read_only=True)
    is_below_passing = serializers.BooleanField(read_only=True)
    graded_by_name = serializers.CharField(source="graded_by.name", read_only=True, default=None)

    class Meta(AssessmentResultSerializer.Meta):
        fields = RESULT_BASE_FIELDS + [
            "submission_status_display",
            "student_name",
            "student_roll_no",
            "section_name",
            "subject_name",
            "assessment_title",
            "total_marks",
            "passing_marks",
            "percentage",
            "is_below_passing",
            "graded_by_name",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


# ---------------------------------------------------------------------------
# Bulk grading (teacher endpoint)
# ---------------------------------------------------------------------------

class BulkResultItemSerializer(serializers.Serializer):
    """One item inside a bulk grade submission."""
    student = serializers.PrimaryKeyRelatedField(
        queryset=__import__("students.models", fromlist=["Student"]).Student.objects.all()
    )
    obtained_marks = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    submission_status = serializers.ChoiceField(
        choices=AssessmentResult.SubmissionStatus.choices,
        default=AssessmentResult.SubmissionStatus.GRADED,
    )
    feedback = serializers.CharField(required=False, allow_blank=True, default="")


class BulkGradeSerializer(serializers.Serializer):
    """
    Payload for bulk grading an entire section.

    {
      "assessment": "<uuid>",
      "results": [
        {"student": "<uuid>", "obtained_marks": 42, "submission_status": "GRADED", "feedback": ""},
        ...
      ]
    }
    """
    assessment = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all()
    )
    results = BulkResultItemSerializer(many=True, min_length=1)


# ---------------------------------------------------------------------------
# Parent homework confirmation
# ---------------------------------------------------------------------------

class ParentHomeworkConfirmSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for the parent-facing homework confirmation endpoint.
    Parents can only toggle parent_confirmed and optionally add a note via feedback.
    """

    class Meta:
        model = AssessmentResult
        fields = ["id", "parent_confirmed", "feedback", "parent_confirmed_at", "parent_confirmed_by"]
        read_only_fields = ["id", "parent_confirmed_at", "parent_confirmed_by"]

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.assessment.task_type != Assessment.TaskType.HOMEWORK:
            raise ValidationError(
                "Parent confirmation is only available for Homework assessments."
            )
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get("parent_confirmed") and not instance.parent_confirmed:
            instance.parent_confirmed_by = self.context["request"].user
            instance.parent_confirmed_at = timezone.now()
        return super().update(instance, validated_data)
