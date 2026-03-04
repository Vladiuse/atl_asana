from django.apps import AppConfig


class FakeMessageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fake_message"
