from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, UUIDModel

def organization_license_upload_path(instance, filename):
    return f"organizations/{instance.id}/licenses/{filename}"

class Organization(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        PENDING = "PENDING", _("Pending")

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
    business_license_image = models.ImageField(
        _("Business License Image"),
        upload_to=organization_license_upload_path,
        blank=True,
        null=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:  # type: ignore
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __str__(self):
        return self.name
