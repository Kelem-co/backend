from importlib import import_module

from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assessments"

    def ready(self):
        import_module("assessments.signals")
