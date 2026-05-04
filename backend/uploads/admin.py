from django.contrib import admin

from backend.uploads.models import MediaFile
from backend.uploads.models import UploadFingerprint


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "file_name",
        "content_type",
        "status",
        "uploaded_by",
        "created_at",
    ]
    list_filter = ["status", "content_type", "created_at"]
    search_fields = ["file_name", "key", "etag"]


@admin.register(UploadFingerprint)
class UploadFingerprintAdmin(admin.ModelAdmin):
    list_display = ["fingerprint", "media_file", "created_at"]
    search_fields = ["fingerprint", "media_file__file_name"]
