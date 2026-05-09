from django.contrib import admin
from schools.models import School, Branch, BranchAdmin

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "country", "status")
    search_fields = ("name", "contact_email", "contact_phone")
    list_filter = ("status", "country")

@admin.register(Branch)
class BranchAdminModel(admin.ModelAdmin):
    list_display = ("name", "school", "city", "status")
    search_fields = ("name", "address", "city", "region")
    list_filter = ("status",)

@admin.register(BranchAdmin)
class BranchAdminUserModel(admin.ModelAdmin):
    list_display = ("user", "branch", "role_title", "status")
    search_fields = ("user__email", "user__name", "role_title")
    list_filter = ("status", "last_login")
