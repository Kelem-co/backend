from rest_framework import serializers
from students.models import Student, ParentStudentLink
from accounts.api.serializers import UserSerializer

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

class ParentStudentLinkSerializer(serializers.ModelSerializer):
    """
    Base serializer for ParentStudentLink.
    """
    class Meta:
        model = ParentStudentLink
        fields = [
            "id", "student", "parent", "relationship_type", 
            "is_primary_contact", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class ParentStudentLinkReadSerializer(ParentStudentLinkSerializer):
    """
    Serializer for reading ParentStudentLink with nested details.
    """
    student_details = StudentSerializer(source="student", read_only=True)
    parent_details = UserSerializer(source="parent", read_only=True)

    class Meta(ParentStudentLinkSerializer.Meta):
        fields = ParentStudentLinkSerializer.Meta.fields + ["student_details", "parent_details"]
