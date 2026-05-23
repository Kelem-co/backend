from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AcademicsConfig(AppConfig):
    name = "academics"
    verbose_name = _("Academics")

    def ready(self):
        import academics.signals  # noqa: F401, PLC0415
