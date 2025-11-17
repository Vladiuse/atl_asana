from django.core.management.base import BaseCommand

from comment_notifier.services import SenderRegistrySynchronizer


class Command(BaseCommand):
    help = "Synchronize senders registry with database"

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        result = SenderRegistrySynchronizer().synchronize()
        self.stdout.write(f"Senders sync result: {result}")
