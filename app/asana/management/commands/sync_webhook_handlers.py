from typing import Any

from django.core.management.base import BaseCommand

from asana.webhook_handlers.synchronizer import WebhookHandlerRegistrySynchronizer


class Command(BaseCommand):
    help = "Synchronize webhook handlers registry with database"

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ANN401
        _ = args, options
        result = WebhookHandlerRegistrySynchronizer().synchronize()
        self.stdout.write(f"Webhook handlers sync result: {result}")
