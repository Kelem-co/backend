from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from core.models import UUIDModel


class Parent(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
        verbose_name=_("User"),
    )
    organizations = models.ManyToManyField(
        "organizations.Organization",
        related_name="parents",
        verbose_name=_("Organizations"),
        blank=True,
    )
    branches = models.ManyToManyField(
        "branches.Branch",
        related_name="parents",
        verbose_name=_("Branches"),
        blank=True,
    )
    secondary_phone_number = models.CharField(
        _("Secondary Phone Number"),
        max_length=20,
        blank=True,
    )
    occupation = models.CharField(_("Occupation"), max_length=255, blank=True)
    work_address = models.CharField(_("Work Address"), max_length=255, blank=True)
    relationship_notes = models.TextField(_("Relationship Notes"), blank=True)
    emergency_contact_name = models.CharField(
        _("Emergency Contact Name"),
        max_length=255,
        blank=True,
    )
    emergency_contact_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=50,
        blank=True,
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Parent")
        verbose_name_plural = _("Parents")
        ordering = ["user__name", "user__email"]

    def __str__(self):
        return self.user.name or self.user.email

    def clean(self):
        super().clean()

        if not self.pk:
            return

        organization_ids = set(
            self.organizations.values_list("id", flat=True),
        )
        invalid_branch = self.branches.exclude(
            organization_id__in=organization_ids,
        ).first()
        if invalid_branch is not None:
            raise ValidationError(
                {
                    "branches": _(
                        "Every assigned branch must belong to one of the "
                        "parent's organizations.",
                    ),
                },
            )


class Student(UUIDModel, TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        WITHDRAWN = "WITHDRAWN", _("Withdrawn")
        GRADUATED = "GRADUATED", _("Graduated")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Organization"),
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Branch"),
    )
    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    gender = models.CharField(_("Gender"), max_length=10, choices=Gender.choices)
    date_of_birth = models.DateField(_("Date of Birth"))
    roll_no = models.CharField(_("Roll Number"), max_length=50, null=True, blank=True)
    current_section = models.ForeignKey(
        "academics.Section",
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name=_("Current Section"),
        null=True,
        blank=True,
    )
    admission_date = models.DateField(_("Admission Date"), null=True, blank=True)
    photo = models.ForeignKey(
        "media.MediaFile",
        verbose_name=_("Photo"),
        on_delete=models.SET_NULL,
        related_name="student_photo_files",
        blank=True,
        null=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        verbose_name = _("Student")
        verbose_name_plural = _("Students")
        unique_together = ("branch", "current_section", "roll_no")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.roll_no})"

    @property
    def parents(self):
        """Returns parent profiles linked to this student."""
        return [
            link.parent
            for link in ParentStudentLink.objects.filter(student=self).select_related(
                "parent__user",
            )
        ]


class ParentStudentLink(UUIDModel, TimeStampedModel):
    class Relationship(models.TextChoices):
        FATHER = "FATHER", _("Father")
        MOTHER = "MOTHER", _("Mother")
        GUARDIAN = "GUARDIAN", _("Guardian")
        OTHER = "OTHER", _("Other")

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="parent_links",
    )
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="student_links",
        verbose_name=_("Parent"),
    )
    relationship_type = models.CharField(
        _("Relationship Type"),
        max_length=20,
        choices=Relationship.choices,
    )
    is_primary_contact = models.BooleanField(_("Is Primary Contact"), default=False)

    class Meta:
        verbose_name = _("Parent Student Link")
        verbose_name_plural = _("Parent Student Links")
        unique_together = ("student", "parent")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.parent.user.name} - "
            f"{self.student.first_name} ({self.relationship_type})"
        )

    def clean(self):
        super().clean()

        if not self.student_id or not self.parent_id:
            return

        if not self.parent.organizations.filter(
            id=self.student.organization_id,
        ).exists():
            raise ValidationError(
                {
                    "parent": _(
                        "The selected parent must belong to the student's "
                        "organization.",
                    ),
                },
            )

        if not self.parent.branches.filter(id=self.student.branch_id).exists():
            raise ValidationError(
                {
                    "parent": _(
                        "The selected parent must belong to the student's branch.",
                    ),
                },
            )
