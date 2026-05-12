from rest_framework import serializers
from rest_framework.exceptions import ValidationError
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

    def validate(self, attrs):
        request = self.context.get("request")
        organization = attrs.get(
            "organization",
            getattr(self.instance, "organization", None),
        )

        if request is None or organization is None:
            return attrs

        if organization.owner_id != request.user.id:
            raise ValidationError(
                {"organization": "You can only manage your own organizations."},
            )

        return attrs
