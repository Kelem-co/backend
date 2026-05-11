from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, UUIDModel

def school_logo_upload_path(instance, filename):
    return f"schools/{instance.id}/logos/{filename}"

class School(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="schools",
        verbose_name=_("Organization"),
    )
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    country = models.CharField(_("Country"), max_length=100)
    contact_email = models.EmailField(_("Contact Email"))
    contact_phone = models.CharField(_("Contact Phone"), max_length=50)
    logo = models.ImageField(
        _("Logo"), upload_to=school_logo_upload_path, blank=True, null=True
    )
    website = models.URLField(_("Website"), blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:  # type: ignore
        verbose_name = _("School")
        verbose_name_plural = _("Schools")

    def __str__(self):
        return self.name
