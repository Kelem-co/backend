from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """

    father_name = forms.CharField(max_length=255)
    grandfather_name = forms.CharField(max_length=255)
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255, required=False)

    def save(self, request):
        user = super().save(request)
        user.father_name = self.cleaned_data["father_name"]
        user.grandfather_name = self.cleaned_data["grandfather_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.address = self.cleaned_data.get("address", "")
        user.save()
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """

    father_name = forms.CharField(max_length=255)
    grandfather_name = forms.CharField(max_length=255)
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255, required=False)

    def save(self, request):
        user = super().save(request)
        user.father_name = self.cleaned_data["father_name"]
        user.grandfather_name = self.cleaned_data["grandfather_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.address = self.cleaned_data.get("address", "")
        user.save()
        return user
