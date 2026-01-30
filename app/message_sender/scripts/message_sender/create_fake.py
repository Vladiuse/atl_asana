import random
from datetime import timedelta

from django.utils import timezone

from message_sender.models import ScheduledMessage, ScheduledMessageStatus


def run() -> None:
    ScheduledMessage.objects.all().delete()
    for i in range(10):
        ScheduledMessage.objects.create(
            status=random.choice([ScheduledMessageStatus.PENDING, ScheduledMessageStatus.SENT]),
            run_at=timezone.now() + timedelta(days=random.randint(1, 10)),
            user_tag=f"user{i}" if i % 2 == 0 else "",
            handler="handler" if i % 2 != 0 else "",
            text=f"Test message {i+1}",
            reference_id=f"leave-{i+1}",
        )