from rest_framework import serializers
from branches.models import Branch, BranchAdmin

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            "id",
            "organization",
            "school",
            "name",
            "address",
            "city",
            "region",
            "contact_phone",
            "contact_email",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class BranchAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchAdmin
        fields = [
            "id",
            "organization",
            "branch",
            "user",
            "emergency_contact_name",
            "emergency_contact_phone",
            "role_title",
            "qualification",
            "status",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_login"]
