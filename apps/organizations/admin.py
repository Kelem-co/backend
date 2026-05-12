from django.contrib import admin
from organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "trade_name", "status", "created_at")
    search_fields = ("name", "trade_name", "license_no", "client_full_name")
    list_filter = ("status", "created_at")
