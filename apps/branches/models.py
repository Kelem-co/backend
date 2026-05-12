from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from schools.models import School

from core.models import TimeStampedModel
from core.models import UUIDModel


class Branch(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="branches",
        verbose_name=_("Organization"),
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="branches",
        verbose_name=_("School"),
    )
    name = models.CharField(_("Branch Name"), max_length=255)
    address = models.TextField(_("Address"))
    city = models.CharField(_("City"), max_length=100)
    region = models.CharField(_("Region"), max_length=100)
    contact_phone = models.CharField(_("Contact Phone"), max_length=50)
    contact_email = models.EmailField(_("Contact Email"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")

    def __str__(self):
        return f"{self.school.name} - {self.name}"


class BranchAdmin(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="branch_admins",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="admins",
        verbose_name=_("Branch"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_admin_profiles",
        verbose_name=_("User"),
    )
    emergency_contact_name = models.CharField(
        _("Emergency Contact Name"),
        max_length=255,
    )
    emergency_contact_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=50,
    )
    role_title = models.CharField(_("Role Title"), max_length=100)
    qualification = models.CharField(_("Qualification"), max_length=255, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    last_login = models.DateTimeField(_("Last Login"), blank=True, null=True)

    class Meta:
        verbose_name = _("Branch Admin")
        verbose_name_plural = _("Branch Admins")

    def __str__(self):
        return f"{self.user.name} - {self.branch.name}"
