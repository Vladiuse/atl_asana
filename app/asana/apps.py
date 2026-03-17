import importlib
import pkgutil

from django.apps import AppConfig, apps


class AsanaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asana"

    def ready(self) -> None:
        from asana import webhook_handlers

        package = webhook_handlers

        # load handlers from common module
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            importlib.import_module(f"{package.__name__}.{module_name}")

        # load handlers from <app>/webhook_actions.py module
        for app_config in apps.get_app_configs():
            try:
                importlib.import_module(f"{app_config.name}.webhook_actions")
            except ModuleNotFoundError:
                continue
