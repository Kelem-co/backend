from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


def organization_license_upload_path(instance, filename):
    return f"organizations/{instance.id}/licenses/{filename}"


class Organization(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        PENDING = "PENDING", _("Pending")

    class VerificationStatus(models.TextChoices):
        VERIFIED = "verified", _("Verified")
        PENDING_MANUAL_REVIEW = "pending_manual_review", _("Pending Manual Review")
        VERIFICATION_UNAVAILABLE = (
            "verification_unavailable",
            _(
                "Verification Unavailable",
            ),
        )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="organizations",
        verbose_name=_("Owner"),
    )
    name = models.CharField(_("Name"), max_length=255)
    trade_name = models.CharField(_("Trade Name"), max_length=255, blank=True)
    tin_number = models.CharField(_("TIN Number"), max_length=20, blank=True)
    license_no = models.CharField(_("License Number"), max_length=100, blank=True)
    client_full_name = models.CharField(_("Client Full Name"), max_length=255)
    business_address = models.TextField(_("Business Address"))
    business_phone_number = models.CharField(_("Business Phone Number"), max_length=50)
    client_phone_number = models.CharField(_("Client Phone Number"), max_length=50)
    business_license_image = models.ForeignKey(
        "media.MediaFile",
        verbose_name=_("Business License Image"),
        on_delete=models.SET_NULL,
        related_name="organization_license_files",
        blank=True,
        null=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    verification_status = models.CharField(
        _("Verification Status"),
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING_MANUAL_REVIEW,
    )
    verification_checked_at = models.DateTimeField(
        _("Verification Checked At"),
        blank=True,
        null=True,
    )
    verification_failure_reason = models.CharField(
        _("Verification Failure Reason"),
        max_length=255,
        blank=True,
    )
    verification_match_source = models.CharField(
        _("Verification Match Source"),
        max_length=100,
        blank=True,
    )
    verified_name = models.CharField(_("Verified Name"), max_length=255, blank=True)
    verified_license_no = models.CharField(
        _("Verified License Number"),
        max_length=100,
        blank=True,
    )
    verified_tin_number = models.CharField(
        _("Verified TIN Number"),
        max_length=20,
        blank=True,
    )

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __str__(self):
        return self.name
