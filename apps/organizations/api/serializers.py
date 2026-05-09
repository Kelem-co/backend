from rest_framework import serializers

from organizations.models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "owner",
            "name",
            "trade_name",
            "license_no",
            "client_full_name",
            "business_address",
            "business_phone_number",
            "client_phone_number",
            "business_license_image",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
