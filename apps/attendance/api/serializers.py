from attendance.models import Attendance
from attendance.models import AttendanceReason
from attendance.models import AttendanceSummary
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# ---------------------------------------------------------------------------
# AttendanceReason
# ---------------------------------------------------------------------------


class AttendanceReasonSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating an absence reason."""

    class Meta:
        model = AttendanceReason
        fields = [
            "id",
            "organization",
            "attendance",
            "reason_category",
            "note",
            "parent_confirmed",
            "confirmed_by",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "confirmed_by",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]


class AttendanceReasonReadSerializer(AttendanceReasonSerializer):
    """Read serializer with human-readable labels."""

    reason_category_display = serializers.CharField(
        source="get_reason_category_display",
        read_only=True,
    )
    confirmed_by_name = serializers.CharField(
        source="confirmed_by.name",
        read_only=True,
        default=None,
    )

    class Meta(AttendanceReasonSerializer.Meta):
        fields = [
            *AttendanceReasonSerializer.Meta.fields,
            "reason_category_display",
            "confirmed_by_name",
        ]


# ---------------------------------------------------------------------------
# Attendance — single record
# ---------------------------------------------------------------------------


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Write serializer — used for individual create/update and as the
    per-item schema inside the bulk endpoint.
    """

    reason = AttendanceReasonReadSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "organization",
            "branch",
            "academic_year",
            "section",
            "student",
            "recorded_by",
            "date",
            "status",
            "remarks",
            "client_side_id",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "recorded_by", "reason", "created_at", "updated_at"]

    def validate(self, attrs):
        # Prevent duplicate records (idempotency via client_side_id is
        # handled at the view level — here we enforce business rules).
        student = attrs.get("student", getattr(self.instance, "student", None))
        section = attrs.get("section", getattr(self.instance, "section", None))

        # Make sure the student belongs to the submitted section
        if student and section and str(student.current_section_id) != str(section.id):
            message = f"Student '{student}' does not belong to section '{section}'."
            raise ValidationError(
                {
                    "student": message,
                },
            )
        return attrs


class AttendanceReadSerializer(AttendanceSerializer):
    """Read serializer — expands all FKs into human-readable fields."""

    student_name = serializers.SerializerMethodField()
    student_roll_no = serializers.CharField(source="student.roll_no", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    grade_name = serializers.CharField(source="section.grade.name", read_only=True)
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    recorded_by_name = serializers.CharField(
        source="recorded_by.name",
        read_only=True,
        default=None,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    needs_reason = serializers.BooleanField(read_only=True)

    class Meta(AttendanceSerializer.Meta):
        fields = [
            *AttendanceSerializer.Meta.fields,
            "student_name",
            "student_roll_no",
            "section_name",
            "grade_name",
            "academic_year_name",
            "branch_name",
            "recorded_by_name",
            "status_display",
            "needs_reason",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}"


# ---------------------------------------------------------------------------
# Bulk attendance submission (teacher endpoint)
# ---------------------------------------------------------------------------


class BulkAttendanceItemSerializer(serializers.Serializer):
    """Schema for a single item inside a bulk attendance submission."""

    student = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "students.models",
            fromlist=["Student"],
        ).Student.objects.all(),
    )
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
    client_side_id = serializers.UUIDField(required=False)


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Submitted by the homeroom teacher once per day for their section.

    Payload shape:
    {
        "section":       "<uuid>",
        "academic_year": "<uuid>",
        "organization":  "<uuid>",
        "branch":        "<uuid>",
        "date":          "YYYY-MM-DD",
        "records": [
            {"student": "<uuid>", "status": "PRESENT", "client_side_id": "<uuid>"},
            ...
        ]
    }
    """

    section = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "academics.models",
            fromlist=["Section"],
        ).Section.objects.all(),
    )
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "academics.models",
            fromlist=["AcademicYear"],
        ).AcademicYear.objects.all(),
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "organizations.models",
            fromlist=["Organization"],
        ).Organization.objects.all(),
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=__import__(
            "branches.models",
            fromlist=["Branch"],
        ).Branch.objects.all(),
    )
    date = serializers.DateField()
    records = BulkAttendanceItemSerializer(many=True, min_length=1)

    def validate_date(self, value):
        if value > timezone.localdate():
            message = "Attendance cannot be submitted for a future date."
            raise ValidationError(message)
        return value


# ---------------------------------------------------------------------------
# Parent reason update
# ---------------------------------------------------------------------------


class ParentReasonUpdateSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for the parent-facing endpoint.
    Parents can only set reason_category, note, and confirm.
    """

    class Meta:
        model = AttendanceReason
        fields = [
            "id",
            "reason_category",
            "note",
            "parent_confirmed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if validated_data.get("parent_confirmed") and not instance.parent_confirmed:
            instance.confirmed_by = self.context["request"].user
            instance.confirmed_at = timezone.now()
        return super().update(instance, validated_data)


class ParentReasonCreateSerializer(serializers.ModelSerializer):
    attendance = serializers.PrimaryKeyRelatedField(
        queryset=Attendance.objects.select_related(
            "student",
            "organization",
        ),
    )

    class Meta:
        model = AttendanceReason
        fields = [
            "id",
            "attendance",
            "reason_category",
            "note",
            "parent_confirmed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        attendance = attrs["attendance"]
        if not attendance.needs_reason:
            raise ValidationError(
                {"attendance": "This attendance record does not require a reason."},
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        attendance = validated_data["attendance"]
        defaults = {
            "organization": attendance.organization,
            "reason_category": validated_data["reason_category"],
            "note": validated_data.get("note", ""),
            "parent_confirmed": validated_data.get("parent_confirmed", True),
        }
        if defaults["parent_confirmed"]:
            defaults["confirmed_by"] = request.user
            defaults["confirmed_at"] = timezone.now()
        else:
            defaults["confirmed_by"] = None
            defaults["confirmed_at"] = None

        reason, _created = AttendanceReason.objects.update_or_create(
            attendance=attendance,
            defaults=defaults,
        )
        return reason


# ---------------------------------------------------------------------------
# AttendanceSummary
# ---------------------------------------------------------------------------


class AttendanceSummarySerializer(serializers.ModelSerializer):
    attendance_rate = serializers.FloatField(read_only=True)
    student_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )

    class Meta:
        model = AttendanceSummary
        fields = [
            "id",
            "organization",
            "student",
            "student_name",
            "academic_year",
            "academic_year_name",
            "total_present",
            "total_absent",
            "total_late",
            "total_excused",
            "total_school_days",
            "attendance_rate",
            "last_updated",
        ]
        read_only_fields = fields  # summary is computed, never written via API

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}"
