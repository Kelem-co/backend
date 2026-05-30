from assessments.models import Assessment
from assessments.models import AssessmentResult
from assessments.models import HomeworkConfirmation
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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

    task_type_display = serializers.CharField(
        source="get_task_type_display",
        read_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Derived from teacher_assignment
    section_name = serializers.CharField(
        source="teacher_assignment.section.name",
        read_only=True,
    )
    grade_name = serializers.CharField(
        source="teacher_assignment.section.grade.name",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="teacher_assignment.subject.name",
        read_only=True,
    )
    subject_code = serializers.CharField(
        source="teacher_assignment.subject.code",
        read_only=True,
    )
    teacher_name = serializers.CharField(
        source="teacher_assignment.teacher.user.name",
        read_only=True,
    )
    teacher_employee_id = serializers.CharField(
        source="teacher_assignment.teacher.employee_id",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="teacher_assignment.academic_year.name",
        read_only=True,
    )
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    result_count = serializers.SerializerMethodField()

    class Meta(AssessmentSerializer.Meta):
        fields = [
            *ASSESSMENT_BASE_FIELDS,
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

    def get_result_count(self, obj) -> int:
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
            "id",
            "graded_by",
            "parent_confirmed_by",
            "parent_confirmed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        assessment = attrs.get("assessment", getattr(self.instance, "assessment", None))
        obtained = attrs.get(
            "obtained_marks",
            getattr(self.instance, "obtained_marks", None),
        )
        if assessment and obtained is not None:
            if obtained > assessment.total_marks:
                raise ValidationError(
                    {"obtained_marks": "Obtained marks cannot exceed total marks."},
                )
        return attrs


class AssessmentResultReadSerializer(AssessmentResultSerializer):
    """Read serializer with expanded details."""

    submission_status_display = serializers.CharField(
        source="get_submission_status_display",
        read_only=True,
    )
    student_name = serializers.SerializerMethodField()
    student_roll_no = serializers.CharField(source="student.roll_no", read_only=True)
    section_name = serializers.CharField(
        source="assessment.teacher_assignment.section.name",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="assessment.teacher_assignment.subject.name",
        read_only=True,
    )
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    total_marks = serializers.DecimalField(
        source="assessment.total_marks",
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )
    passing_marks = serializers.DecimalField(
        source="assessment.passing_marks",
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )
    percentage = serializers.FloatField(read_only=True)
    is_below_passing = serializers.BooleanField(read_only=True)
    graded_by_name = serializers.CharField(
        source="graded_by.name",
        read_only=True,
        default=None,
    )
    assessment_description = serializers.CharField(
        source="assessment.description",
        read_only=True,
    )
    assessment_due_date = serializers.DateField(
        source="assessment.due_date",
        read_only=True,
    )
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    assessment_id = serializers.UUIDField(source="assessment.id", read_only=True)
    branch_id = serializers.UUIDField(source="assessment.branch.id", read_only=True)
    branch_name = serializers.CharField(source="assessment.branch.name", read_only=True)
    subject_id = serializers.UUIDField(
        source="assessment.teacher_assignment.subject.id",
        read_only=True,
    )
    section_id = serializers.UUIDField(
        source="assessment.teacher_assignment.section.id",
        read_only=True,
    )
    homework_confirmation = serializers.SerializerMethodField()

    class Meta(AssessmentResultSerializer.Meta):
        fields = [
            *RESULT_BASE_FIELDS,
            "submission_status_display",
            "student_name",
            "student_roll_no",
            "section_name",
            "subject_name",
            "assessment_title",
            "assessment_description",
            "assessment_due_date",
            "student_id",
            "assessment_id",
            "branch_id",
            "branch_name",
            "subject_id",
            "total_marks",
            "passing_marks",
            "percentage",
            "is_below_passing",
            "graded_by_name",
            "section_id",
            "homework_confirmation",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_homework_confirmation(self, obj):
        confirmation = getattr(obj, "homework_confirmation", None)
        if confirmation is None:
            return None
        return {
            "id": str(confirmation.id),
            "is_confirmed": confirmation.is_confirmed,
            "feedback": confirmation.feedback,
            "confirmed_at": confirmation.confirmed_at,
        }


# ---------------------------------------------------------------------------
# Bulk grading (teacher endpoint)
# ---------------------------------------------------------------------------


class BulkResultItemSerializer(serializers.Serializer):
    """One item inside a bulk grade submission."""

    student = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "students.models",
            fromlist=["Student"],
        ).Student.objects.all(),
    )
    obtained_marks = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
    )
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
        {
          "student": "<uuid>",
          "obtained_marks": 42,
          "submission_status": "GRADED",
          "feedback": ""
        },
        ...
      ]
    }
    """

    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())
    results = BulkResultItemSerializer(many=True, min_length=1)

    def validate(self, attrs):
        assessment = attrs["assessment"]
        section_id = assessment.teacher_assignment.section_id

        for item in attrs["results"]:
            student = item["student"]
            if student.current_section_id != section_id:
                raise ValidationError(
                    {
                        "results": (
                            f"Student '{student}' does not belong to "
                            f"assessment section '{assessment.section}'."
                        ),
                    },
                )

            obtained = item.get("obtained_marks")
            if obtained is not None and obtained > assessment.total_marks:
                raise ValidationError(
                    {
                        "results": (
                            "Obtained marks cannot exceed total marks "
                            f"for student '{student}'."
                        ),
                    },
                )

        return attrs


# ---------------------------------------------------------------------------
# Parent homework confirmation
# ---------------------------------------------------------------------------


class ParentHomeworkConfirmSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for the parent-facing homework confirmation endpoint.
    Parents can only toggle parent_confirmed and optionally add a note via feedback.
    """

    NON_HOMEWORK_CONFIRMATION_ERROR = (
        "Parent confirmation is only available for Homework assessments."
    )

    class Meta:
        model = AssessmentResult
        fields = [
            "id",
            "parent_confirmed",
            "feedback",
            "parent_confirmed_at",
            "parent_confirmed_by",
        ]
        read_only_fields = ["id", "parent_confirmed_at", "parent_confirmed_by"]

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.assessment.task_type != Assessment.TaskType.HOMEWORK:
            error_message = self.NON_HOMEWORK_CONFIRMATION_ERROR
            raise ValidationError(error_message)
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get("parent_confirmed") and not instance.parent_confirmed:
            instance.parent_confirmed_by = self.context["request"].user
            instance.parent_confirmed_at = timezone.now()
        return super().update(instance, validated_data)


class HomeworkConfirmationSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.select_related(
            "teacher_assignment__section",
            "organization",
            "branch",
        ),
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "students.models",
            fromlist=["Student"],
        ).Student.objects.select_related("current_section", "organization", "branch"),
    )

    class Meta:
        model = HomeworkConfirmation
        validators = []
        fields = [
            "id",
            "organization",
            "branch",
            "section",
            "assessment",
            "student",
            "is_confirmed",
            "confirmed_at",
            "feedback",
            "confirmed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "branch",
            "section",
            "confirmed_at",
            "confirmed_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        assessment = attrs["assessment"]
        student = attrs["student"]
        if assessment.task_type != Assessment.TaskType.HOMEWORK:
            raise ValidationError(
                {"assessment": "Only homework assessments can be confirmed."},
            )
        if student.branch_id != assessment.branch_id:
            raise ValidationError(
                {
                    "student": (
                        "Student must belong to the same branch as the assessment."
                    ),
                },
            )
        if student.organization_id != assessment.organization_id:
            raise ValidationError(
                {
                    "student": (
                        "Student must belong to the same organization as the "
                        "assessment."
                    ),
                },
            )
        if student.current_section_id != assessment.teacher_assignment.section_id:
            raise ValidationError(
                {"student": "Student must belong to the assessment's section."},
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        assessment = validated_data["assessment"]
        student = validated_data["student"]
        existing_confirmation = HomeworkConfirmation.objects.filter(
            assessment=assessment,
            student=student,
        ).first()
        defaults = {
            "organization": assessment.organization,
            "branch": assessment.branch,
            "section": assessment.teacher_assignment.section,
            "assessment": assessment,
            "student": student,
            "is_confirmed": validated_data["is_confirmed"],
            "feedback": validated_data.get("feedback", ""),
        }
        if defaults["is_confirmed"]:
            defaults["confirmed_at"] = (
                existing_confirmation.confirmed_at
                if existing_confirmation and existing_confirmation.confirmed_at
                else timezone.now()
            )
            defaults["confirmed_by"] = request.user
        else:
            defaults["confirmed_at"] = None
            defaults["confirmed_by"] = None

        confirmation, _created = HomeworkConfirmation.objects.update_or_create(
            assessment=assessment,
            student=student,
            defaults=defaults,
        )
        confirmation.full_clean()
        confirmation.save()
        return confirmation


class TodaysHomeworkReadSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="assessment.id")
    title = serializers.CharField(source="assessment.title")
    description = serializers.CharField(source="assessment.description")
    due_date = serializers.DateField(source="assessment.due_date")
    teacher_name = serializers.CharField(
        source="assessment.teacher_assignment.teacher.user.name",
    )
    subject_name = serializers.CharField(
        source="assessment.teacher_assignment.subject.name",
    )
    section_name = serializers.CharField(
        source="assessment.teacher_assignment.section.name",
    )
    branch_id = serializers.UUIDField(source="assessment.branch.id")
    branch_name = serializers.CharField(source="assessment.branch.name")
    student_id = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_roll_no = serializers.SerializerMethodField()
    confirmed = serializers.BooleanField()
    homework_confirmation = serializers.SerializerMethodField()

    def get_student_id(self, obj):
        student = obj.get("student")
        if student is None:
            return None
        return str(student.id)

    def get_student_name(self, obj) -> str:
        student = obj["student"]
        if student is None:
            return None
        return f"{student.first_name} {student.last_name}"

    def get_student_roll_no(self, obj):
        student = obj.get("student")
        if student is None:
            return None
        return student.roll_no

    def get_homework_confirmation(self, obj):
        confirmation = obj.get("homework_confirmation")
        if confirmation is None:
            return None
        return {
            "id": str(confirmation.id),
            "is_confirmed": confirmation.is_confirmed,
            "feedback": confirmation.feedback,
            "confirmed_at": confirmation.confirmed_at,
        }
