from rest_framework import serializers
from teachers.models import HomeroomAssignment
from teachers.models import Teacher
from teachers.models import TeacherQualification
from teachers.models import TeacherSubjectAssignment

from media.api.serializers import MediaFileReferenceField

# ---------------------------------------------------------------------------
# Qualification
# ---------------------------------------------------------------------------


class TeacherQualificationSerializer(serializers.ModelSerializer):
    certificate_copy = MediaFileReferenceField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TeacherQualification
        fields = [
            "id",
            "teacher",
            "organization",
            "degree_name",
            "institution",
            "field_of_study",
            "completion_date",
            "certificate_copy",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Teacher
# ---------------------------------------------------------------------------


class TeacherSerializer(serializers.ModelSerializer):
    """Write serializer (used for create / update)."""

    qualifications = TeacherQualificationSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "organization",
            "branch",
            "employee_id",
            "bio",
            "specialization",
            "joining_date",
            "qualifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# TeacherSubjectAssignment
# ---------------------------------------------------------------------------


class TeacherSubjectAssignmentSerializer(serializers.ModelSerializer):
    """Write serializer (FK ids only)."""

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            "id",
            "teacher",
            "organization",
            "subject",
            "section",
            "academic_year",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TeacherSubjectAssignmentReadSerializer(TeacherSubjectAssignmentSerializer):
    """Read serializer with expanded nested details."""

    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    teacher_employee_id = serializers.CharField(
        source="teacher.employee_id",
        read_only=True,
    )
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    grade_name = serializers.CharField(source="subject.grade.name", read_only=True)
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )

    class Meta(TeacherSubjectAssignmentSerializer.Meta):
        fields = [
            *TeacherSubjectAssignmentSerializer.Meta.fields,
            "teacher_name",
            "teacher_employee_id",
            "subject_name",
            "subject_code",
            "section_name",
            "grade_name",
            "academic_year_name",
        ]


# ---------------------------------------------------------------------------
# Custom: section schedule response shape
# ---------------------------------------------------------------------------


class SectionTeacherScheduleSerializer(serializers.ModelSerializer):
    """
    Purpose-built read serializer for the by-section endpoint.
    Returns: subject info + the teacher who teaches it in that section.
    """

    subject_id = serializers.UUIDField(source="subject.id", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    grade_name = serializers.CharField(source="subject.grade.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    teacher_id = serializers.UUIDField(source="teacher.id", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    teacher_employee_id = serializers.CharField(
        source="teacher.employee_id",
        read_only=True,
    )
    teacher_specialization = serializers.CharField(
        source="teacher.specialization",
        read_only=True,
    )

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            "id",
            "section_name",
            "academic_year_name",
            "subject_id",
            "subject_name",
            "subject_code",
            "grade_name",
            "teacher_id",
            "teacher_name",
            "teacher_employee_id",
            "teacher_specialization",
        ]


# ---------------------------------------------------------------------------
# Homeroom Assignment
# ---------------------------------------------------------------------------


class HomeroomAssignmentSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids for create / update."""

    class Meta:
        model = HomeroomAssignment
        fields = [
            "id",
            "organization",
            "branch",
            "academic_year",
            "section",
            "teacher",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HomeroomAssignmentReadSerializer(HomeroomAssignmentSerializer):
    """
    Read serializer — flattens all related objects so the consumer gets
    human-readable details instead of bare UUIDs.
    """

    # Teacher details
    teacher_id = serializers.UUIDField(source="teacher.id", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    teacher_email = serializers.EmailField(source="teacher.user.email", read_only=True)
    teacher_phone = serializers.CharField(
        source="teacher.user.phone_number",
        read_only=True,
    )
    teacher_employee_id = serializers.CharField(
        source="teacher.employee_id",
        read_only=True,
    )
    teacher_specialization = serializers.CharField(
        source="teacher.specialization",
        read_only=True,
    )
    teacher_branch = serializers.CharField(source="teacher.branch.name", read_only=True)

    # Section details
    section_name = serializers.CharField(source="section.name", read_only=True)
    grade_name = serializers.CharField(source="section.grade.name", read_only=True)

    # Academic year details
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    academic_year_start = serializers.DateField(
        source="academic_year.start_date",
        read_only=True,
    )
    academic_year_end = serializers.DateField(
        source="academic_year.end_date",
        read_only=True,
    )

    # Branch & org names
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta(HomeroomAssignmentSerializer.Meta):
        fields = [
            *HomeroomAssignmentSerializer.Meta.fields,
            "teacher_id",
            "teacher_name",
            "teacher_email",
            "teacher_phone",
            "teacher_employee_id",
            "teacher_specialization",
            "teacher_branch",
            "section_name",
            "grade_name",
            "academic_year_name",
            "academic_year_start",
            "academic_year_end",
            "branch_name",
            "organization_name",
        ]
