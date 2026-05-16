from organizations.models import Organization
from rest_framework import serializers


class OrganizationSerializer(serializers.ModelSerializer):
    requires_manual_verification = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "owner",
            "name",
            "trade_name",
            "tin_number",
            "license_no",
            "client_full_name",
            "business_address",
            "business_phone_number",
            "client_phone_number",
            "business_license_image",
            "status",
            "verification_status",
            "verification_checked_at",
            "verification_failure_reason",
            "verification_match_source",
            "verified_name",
            "verified_license_no",
            "verified_tin_number",
            "requires_manual_verification",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "status",
            "verification_status",
            "verification_checked_at",
            "verification_failure_reason",
            "verification_match_source",
            "verified_name",
            "verified_license_no",
            "verified_tin_number",
            "requires_manual_verification",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        if self.instance is None and not str(attrs.get("tin_number", "")).strip():
            msg = "TIN number is required when creating an organization."
            raise serializers.ValidationError({"tin_number": msg})
        return attrs

    def validate_tin_number(self, value: str) -> str:
        return value

    def get_requires_manual_verification(self, obj: Organization) -> bool:
        return obj.verification_status != Organization.VerificationStatus.VERIFIED
