from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel, UUIDModel
from django.conf import settings

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
    gender = models.CharField(
        _("Gender"), max_length=10, choices=Gender.choices
    )
    date_of_birth = models.DateField(_("Date of Birth"))
    roll_no = models.CharField(_("Roll Number"), max_length=50)
    current_section = models.ForeignKey(
        "academics.Section",
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name=_("Current Section"),
    )
    admission_date = models.DateField(_("Admission Date"))
    photo = models.ImageField(_("Photo"), upload_to="students/photos/", blank=True, null=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=Status.choices, default=Status.ACTIVE
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
        """Returns parent users linked to this student."""
        return [link.parent for link in ParentStudentLink.objects.filter(student=self).select_related("parent")]

class ParentStudentLink(UUIDModel, TimeStampedModel):
    class Relationship(models.TextChoices):
        FATHER = "FATHER", _("Father")
        MOTHER = "MOTHER", _("Mother")
        GUARDIAN = "GUARDIAN", _("Guardian")
        OTHER = "OTHER", _("Other")

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="parent_links"
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_links",
        verbose_name=_("Parent"),
    )
    relationship_type = models.CharField(
        _("Relationship Type"), max_length=20, choices=Relationship.choices
    )
    is_primary_contact = models.BooleanField(_("Is Primary Contact"), default=False)

    class Meta:
        verbose_name = _("Parent Student Link")
        verbose_name_plural = _("Parent Student Links")
        unique_together = ("student", "parent")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.parent.name} - {self.student.first_name} ({self.relationship_type})"

