from django.contrib import admin
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "trade_name",
        "tin_number",
        "license_no",
        "status",
        "verification_status",
        "verification_checked_at",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "verification_checked_at",
        "verification_match_source",
        "verified_name",
        "verified_license_no",
        "verified_tin_number",
        "review_actions",
    )
    search_fields = (
        "name",
        "trade_name",
        "tin_number",
        "license_no",
        "client_full_name",
        "verified_name",
        "verified_license_no",
        "verified_tin_number",
    )
    list_filter = (
        "status",
        "verification_status",
        "created_at",
        "verification_checked_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
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
                ),
            },
        ),
        (
            "Review Status",
            {
                "fields": (
                    "status",
                    "verification_status",
                    "verification_failure_reason",
                    "verification_checked_at",
                    "verification_match_source",
                    "verified_name",
                    "verified_license_no",
                    "verified_tin_number",
                    "review_actions",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:object_id>/approve/",
                self.admin_site.admin_view(self.approve_view),
                name="organizations_organization_approve",
            ),
            path(
                "<uuid:object_id>/send-to-review/",
                self.admin_site.admin_view(self.send_to_review_view),
                name="organizations_organization_send_to_review",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Review Actions")
    def review_actions(self, obj: Organization) -> str:
        approve_url = reverse(
            "admin:organizations_organization_approve",
            kwargs={"object_id": obj.pk},
        )
        review_url = reverse(
            "admin:organizations_organization_send_to_review",
            kwargs={"object_id": obj.pk},
        )
        return format_html(
            '<a class="button" href="{}">Approve</a>&nbsp;'
            '<a class="button" href="{}">Send To Review</a>',
            approve_url,
            review_url,
        )

    def approve_view(
        self,
        request: HttpRequest,
        object_id: str,
    ) -> HttpResponseRedirect:
        organization = get_object_or_404(Organization, pk=object_id)
        organization.status = Organization.Status.ACTIVE
        organization.verification_status = Organization.VerificationStatus.VERIFIED
        organization.verification_failure_reason = ""
        organization.verification_checked_at = timezone.now()
        organization.save(
            update_fields=[
                "status",
                "verification_status",
                "verification_failure_reason",
                "verification_checked_at",
                "updated_at",
            ],
        )
        self.message_user(request, "Organization approved successfully.")
        return HttpResponseRedirect(
            reverse(
                "admin:organizations_organization_change",
                kwargs={"object_id": organization.pk},
            ),
        )

    def send_to_review_view(
        self,
        request: HttpRequest,
        object_id: str,
    ) -> HttpResponseRedirect:
        organization = get_object_or_404(Organization, pk=object_id)
        organization.status = Organization.Status.PENDING
        organization.verification_status = (
            Organization.VerificationStatus.PENDING_MANUAL_REVIEW
        )
        if not organization.verification_failure_reason:
            organization.verification_failure_reason = "manual_review_required"
        organization.verification_checked_at = timezone.now()
        organization.save(
            update_fields=[
                "status",
                "verification_status",
                "verification_failure_reason",
                "verification_checked_at",
                "updated_at",
            ],
        )
        self.message_user(request, "Organization moved to manual review.")
        return HttpResponseRedirect(
            reverse(
                "admin:organizations_organization_change",
                kwargs={"object_id": organization.pk},
            ),
        )
