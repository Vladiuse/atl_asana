from django.apps import AppConfig


class CommentNotifierConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comment_notifier"

    def ready(self) -> None:
        from .services import SenderRegistrySynchronizer

        SenderRegistrySynchronizer().synchronize()
