import importlib

from django.apps import AppConfig


class MediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "media"
    verbose_name = "Media Upload"

    def ready(self) -> None:
        importlib.import_module("media.signals")
