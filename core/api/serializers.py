from __future__ import annotations

from rest_framework import serializers


class ApiErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    field = serializers.CharField(allow_null=True, required=False)


class ApiErrorResponseSerializer(serializers.Serializer):
    errors = ApiErrorSerializer(many=True)


class EmptyDataResponseSerializer(serializers.Serializer):
    data = serializers.JSONField(allow_null=True)
    message = serializers.CharField()


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        from core.models import ImportJob
        model = ImportJob
        fields = ["id", "status", "task_id", "progress", "errors", "module", "created_at", "updated_at"]
