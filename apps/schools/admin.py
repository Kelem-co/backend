from django.contrib import admin
from schools.models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "country", "status")
    search_fields = ("name", "description", "contact_email", "contact_phone")
    list_filter = ("status", "country")
