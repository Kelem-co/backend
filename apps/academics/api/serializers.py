from academics.models import AcademicYear
from academics.models import Grade
from academics.models import GradeSubject
from academics.models import Section
from academics.models import Subject
from rest_framework import serializers


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
