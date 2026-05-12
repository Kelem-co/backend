from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BranchesConfig(AppConfig):
    name = "branches"
    verbose_name = _("Branches")
