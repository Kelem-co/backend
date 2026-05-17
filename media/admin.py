from __future__ import annotations

from django.contrib import admin

from .models import MediaFile
from .models import UploadFingerprint


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "file_name",
        "status",
        "uploaded_by",
        "size",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "content_type", "created_at", "uploaded_by"]
    search_fields = ["file_name", "key", "id"]
    readonly_fields = [
        "id",
        "key",
        "etag",
        "created_at",
        "updated_at",
        "size",
    ]
    fieldsets = (
        (
            "Upload Info",
            {"fields": ("id", "file_name", "content_type", "uploaded_by")},
        ),
        (
            "Storage",
            {"fields": ("key", "bucket", "size", "etag")},
        ),
        (
            "Status",
            {"fields": ("status",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    ordering = ["-created_at"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(UploadFingerprint)
class UploadFingerprintAdmin(admin.ModelAdmin):
    list_display = [
        "fingerprint",
        "media_file",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["fingerprint", "media_file__file_name"]
    readonly_fields = ["fingerprint", "media_file", "created_at"]
    ordering = ["-created_at"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
