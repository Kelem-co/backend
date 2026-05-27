from academics.models import AcademicYear
from academics.models import CalendarDocument
from academics.models import Grade
from academics.models import GradeSubject
from academics.models import Section
from academics.models import Subject
from branches.models import Branch
from organizations.models import Organization
from rest_framework import serializers

from media.api.serializers import MediaFileReferenceField


def validate_calendar_document_scope(attrs):
    organization = attrs["organization"]
    branch = attrs["branch"]
    academic_year = attrs.get("academic_year")

    if branch.organization_id != organization.id:
        raise serializers.ValidationError(
            {
                "branch": (
                    "Selected branch does not belong to the selected organization."
                ),
            },
        )

    if academic_year is not None:
        if academic_year.organization_id != organization.id:
            raise serializers.ValidationError(
                {
                    "academic_year": (
                        "Selected academic year does not belong to the selected "
                        "organization."
                    ),
                },
            )
        if academic_year.branch_id != branch.id:
            raise serializers.ValidationError(
                {
                    "academic_year": (
                        "Selected academic year does not belong to the selected branch."
                    ),
                },
            )

    return attrs


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class GradeSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSubject
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class GradeSubjectReadSerializer(GradeSubjectSerializer):
    """Read-only serializer with nested grade and subject details."""

    grade_details = GradeSerializer(source="grade", read_only=True)
    subject_details = SubjectSerializer(source="subject", read_only=True)

    class Meta(GradeSubjectSerializer.Meta):
        fields = GradeSubjectSerializer.Meta.fields


class CalendarDocumentSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    media_file = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = CalendarDocument
        fields = [
            "id",
            "organization",
            "branch",
            "academic_year",
            "media_file",
            "file_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "file_name", "created_at", "updated_at"]

    def get_file_name(self, obj: CalendarDocument) -> str | None:
        if obj.media_file is None:
            return None
        return obj.media_file.file_name

    def get_organization(self, obj: CalendarDocument) -> str:
        return str(obj.organization_id)

    def get_branch(self, obj: CalendarDocument) -> str:
        return str(obj.branch_id)

    def get_academic_year(self, obj: CalendarDocument) -> str | None:
        if obj.academic_year_id is None:
            return None
        return str(obj.academic_year_id)

    def get_media_file(self, obj: CalendarDocument) -> str | None:
        if obj.media_file_id is None:
            return None
        return str(obj.media_file_id)


class CalendarDocumentUpsertSerializer(serializers.Serializer):
    media_file = MediaFileReferenceField(content_type_prefix="application/pdf")
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.select_related("organization"),
    )
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.select_related("organization", "branch"),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        return validate_calendar_document_scope(attrs)


class CalendarDocumentCurrentQuerySerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.select_related("organization"),
    )
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.select_related("organization", "branch"),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        return validate_calendar_document_scope(attrs)
