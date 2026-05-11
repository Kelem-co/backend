from rest_framework import serializers

from schools.models import School

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "country",
            "contact_email",
            "contact_phone",
            "logo",
            "website",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
