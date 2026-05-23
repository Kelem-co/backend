from accounts.api.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from students.models import Parent
from students.models import ParentStudentLink
from students.models import Student

from media.api.serializers import MediaFileReferenceField

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

PARENT_BASE_FIELDS = [
    "id",
    "user",
    "organizations",
    "branches",
    "secondary_phone_number",
    "occupation",
    "work_address",
    "relationship_notes",
    "emergency_contact_name",
    "emergency_contact_phone",
    "is_active",
    "created_at",
    "updated_at",
]


class StudentSerializer(serializers.ModelSerializer):
    """Write serializer — accepts FK ids for create / update."""

    photo = MediaFileReferenceField(
        required=False,
        allow_null=True,
        content_type_prefix="image/",
    )

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
    grade_name = serializers.CharField(
        source="current_section.grade.name",
        read_only=True,
    )
    grade_level = serializers.IntegerField(
        source="current_section.grade.level",
        read_only=True,
    )

    # Academic year attached to the section (nullable on Section)
    academic_year_id = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()

    # Branch
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    # Organization
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta(StudentSerializer.Meta):
        fields = [
            *STUDENT_BASE_FIELDS,
            "section_name",
            "grade_id",
            "grade_name",
            "grade_level",
            "academic_year_id",
            "academic_year_name",
            "branch_name",
            "organization_name",
        ]

    def get_academic_year_id(self, obj) -> str | None:
        yr = obj.current_section.academic_year
        return str(yr.id) if yr else None

    def get_academic_year_name(self, obj) -> str | None:
        yr = obj.current_section.academic_year
        return yr.name if yr else None


class ParentSerializer(serializers.ModelSerializer):
    """Write serializer for parent profiles."""

    class Meta:
        model = Parent
        fields = PARENT_BASE_FIELDS
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        organizations = attrs.get("organizations")
        branches = attrs.get("branches")

        if user and getattr(user, "role", "") != user.Role.PARENT:
            attrs["user"].role = user.Role.PARENT

        if self.instance is not None and organizations is None:
            organizations = self.instance.organizations.all()
        if self.instance is not None and branches is None:
            branches = self.instance.branches.all()

        if organizations is not None and branches is not None:
            organization_ids = {organization.id for organization in organizations}
            invalid_branch = next(
                (
                    branch
                    for branch in branches
                    if branch.organization_id not in organization_ids
                ),
                None,
            )
            if invalid_branch is not None:
                raise ValidationError(
                    {
                        "branches": (
                            "Every assigned branch must belong to one of the "
                            "selected organizations."
                        ),
                    },
                )

        return attrs

    def create(self, validated_data):
        organizations = validated_data.pop("organizations", [])
        branches = validated_data.pop("branches", [])
        user = validated_data["user"]
        user.role = user.Role.PARENT
        user.save(update_fields=["role"])
        parent = Parent.objects.create(**validated_data)
        parent.organizations.set(organizations)
        parent.branches.set(branches)
        parent.full_clean()
        return parent

    def update(self, instance, validated_data):
        organizations = validated_data.pop("organizations", None)
        branches = validated_data.pop("branches", None)

        user = validated_data.get("user")
        if user is not None and user.role != user.Role.PARENT:
            user.role = user.Role.PARENT
            user.save(update_fields=["role"])

        instance = super().update(instance, validated_data)
        if organizations is not None:
            instance.organizations.set(organizations)
        if branches is not None:
            instance.branches.set(branches)
        instance.full_clean()
        return instance


class ParentReadSerializer(ParentSerializer):
    """Read serializer with user, organization, branch, and student details."""

    user_details = UserSerializer(source="user", read_only=True)
    organization_details = serializers.SerializerMethodField()
    branch_details = serializers.SerializerMethodField()
    student_details = serializers.SerializerMethodField()

    class Meta(ParentSerializer.Meta):
        fields = [
            *PARENT_BASE_FIELDS,
            "user_details",
            "organization_details",
            "branch_details",
            "student_details",
        ]

    def get_organization_details(self, obj) -> list[dict]:
        return [
            {
                "id": str(organization.id),
                "name": organization.name,
                "status": organization.status,
            }
            for organization in obj.organizations.all()
        ]

    def get_branch_details(self, obj) -> list[dict]:
        return [
            {
                "id": str(branch.id),
                "name": branch.name,
                "organization": str(branch.organization_id),
                "status": branch.status,
            }
            for branch in obj.branches.all()
        ]

    def get_student_details(self, obj) -> list[dict]:
        return [
            {
                "id": str(link.student.id),
                "first_name": link.student.first_name,
                "last_name": link.student.last_name,
                "roll_no": link.student.roll_no,
                "branch": str(link.student.branch_id),
                "organization": str(link.student.organization_id),
                "relationship_type": link.relationship_type,
                "is_primary_contact": link.is_primary_contact,
            }
            for link in obj.student_links.select_related("student")
        ]


# ---------------------------------------------------------------------------
# ParentStudentLink
# ---------------------------------------------------------------------------


class ParentStudentLinkSerializer(serializers.ModelSerializer):
    """Base serializer for ParentStudentLink."""

    class Meta:
        model = ParentStudentLink
        fields = [
            "id",
            "student",
            "parent",
            "relationship_type",
            "is_primary_contact",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))

        if student is None or parent is None:
            return attrs

        if not parent.organizations.filter(id=student.organization_id).exists():
            raise ValidationError(
                {
                    "parent": (
                        "The selected parent must belong to the student's organization."
                    ),
                },
            )

        if not parent.branches.filter(id=student.branch_id).exists():
            raise ValidationError(
                {
                    "parent": (
                        "The selected parent must belong to the student's branch."
                    ),
                },
            )

        return attrs


class ParentStudentLinkReadSerializer(ParentStudentLinkSerializer):
    """Serializer for reading ParentStudentLink with nested details."""

    student_details = StudentReadSerializer(source="student", read_only=True)
    parent_details = ParentReadSerializer(source="parent", read_only=True)

    class Meta(ParentStudentLinkSerializer.Meta):
        fields = [
            *ParentStudentLinkSerializer.Meta.fields,
            "student_details",
            "parent_details",
        ]


class BulkImportSerializer(serializers.Serializer):
    file = MediaFileReferenceField()
    organization = serializers.UUIDField()
    branch = serializers.UUIDField()
