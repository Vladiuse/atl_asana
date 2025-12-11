import importlib
import pkgutil

from django.apps import AppConfig


class AsanaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asana"

    def ready(self) -> None:
        from asana import webhook_handlers

        package = webhook_handlers

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            importlib.import_module(f"{package.__name__}.{module_name}")
