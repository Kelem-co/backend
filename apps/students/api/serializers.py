from rest_framework import serializers
from students.models import Student, ParentStudentLink

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

class ParentStudentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentStudentLink
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
