from rest_framework import serializers
from students.models import Student, ParentStudentLink
from accounts.api.serializers import UserSerializer


# Base field list derived from the Student model — kept explicit so
# StudentReadSerializer can safely extend it without iterating "__all__".
STUDENT_BASE_FIELDS = [
    "id",
    "organization",
    "branch",
    "first_name",
    "last_name",
    "gender",
    "date_of_birth",
    "roll_no",
    "current_section",
    "admission_date",
    "photo",
    "status",
    "created_at",
    "updated_at",
]


class StudentSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids for create / update."""

    class Meta:
        model = Student
        fields = STUDENT_BASE_FIELDS
        read_only_fields = ["id", "created_at", "updated_at"]


class StudentReadSerializer(StudentSerializer):
    """
    Read serializer — all student fields plus human-readable details for
    every related object so callers never need a follow-up request.
    """

    # Section
    section_name = serializers.CharField(source="current_section.name", read_only=True)

    # Grade (via section)
    grade_id = serializers.UUIDField(source="current_section.grade.id", read_only=True)
    grade_name = serializers.CharField(source="current_section.grade.name", read_only=True)
    grade_level = serializers.IntegerField(source="current_section.grade.level", read_only=True)

    # Academic year attached to the section (nullable on Section)
    academic_year_id = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()

    # Branch
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    # Organization
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta(StudentSerializer.Meta):
        fields = STUDENT_BASE_FIELDS + [
            "section_name",
            "grade_id",
            "grade_name",
            "grade_level",
            "academic_year_id",
            "academic_year_name",
            "branch_name",
            "organization_name",
        ]

    def get_academic_year_id(self, obj):
        yr = obj.current_section.academic_year
        return str(yr.id) if yr else None

    def get_academic_year_name(self, obj):
        yr = obj.current_section.academic_year
        return yr.name if yr else None


# ---------------------------------------------------------------------------
# ParentStudentLink
# ---------------------------------------------------------------------------

class ParentStudentLinkSerializer(serializers.ModelSerializer):
    """Base serializer for ParentStudentLink."""

    class Meta:
        model = ParentStudentLink
        fields = [
            "id", "student", "parent", "relationship_type",
            "is_primary_contact", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ParentStudentLinkReadSerializer(ParentStudentLinkSerializer):
    """Serializer for reading ParentStudentLink with nested details."""

    student_details = StudentReadSerializer(source="student", read_only=True)
    parent_details = UserSerializer(source="parent", read_only=True)

    class Meta(ParentStudentLinkSerializer.Meta):
        fields = ParentStudentLinkSerializer.Meta.fields + ["student_details", "parent_details"]
