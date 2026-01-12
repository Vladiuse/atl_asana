from django.core.management.base import BaseCommand

from asana.webhook_handlers.synchronizer import WebhookHandlerRegistrySynchronizer


class Command(BaseCommand):
    help = "Synchronize webhook handlers registry with database"

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003, ARG002
        result = WebhookHandlerRegistrySynchronizer().synchronize()
        self.stdout.write(f"Webhook handlers sync result: {result}")
