from rest_framework import serializers
from analytics.models import InterventionLog


class InterventionLogSerializer(serializers.ModelSerializer):
    intervention_type_display = serializers.CharField(
        source="get_intervention_type_display", read_only=True
    )
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = InterventionLog
        fields = [
            "id",
            "organization",
            "student",
            "student_name",
            "intervention_type",
            "intervention_type_display",
            "severity",
            "severity_display",
            "status",
            "status_display",
            "source_model",
            "source_id",
            "title",
            "description",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
