from typing import Any

from django.core.management.base import BaseCommand

from comment_notifier.services import SenderRegistrySynchronizer


class Command(BaseCommand):
    help = "Synchronize senders registry with database"

    def handle(self, *args: str, **options: Any) -> None:  # noqa: ANN401
        _ = args
        _ = options
        result = SenderRegistrySynchronizer().synchronize()
        self.stdout.write(f"Senders sync result: {result}")
