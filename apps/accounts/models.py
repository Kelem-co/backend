from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import CharField, DateTimeField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, UUIDModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(UUIDModel, TimeStampedModel, AbstractUser):
    """
    Default custom user model for core.
    """
    
    username = None
    email = EmailField(_("Email Address"), unique=True)
    name = CharField(_("First Name"), blank=True, max_length=255)
    father_name = CharField(_("Father's Name"), blank=True, max_length=255)
    grandfather_name = CharField(_("Grandfather's Name"), blank=True, max_length=255)
    phone_number = CharField(_("Phone Number"), null=True, blank=True, unique=True, max_length=20)
    address = CharField(_("Address"), blank=True, max_length=255)
    verified_at = DateTimeField(_("Verified At"), blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager() # type: ignore[assignment]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.pk})