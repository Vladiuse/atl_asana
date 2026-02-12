from celery import Task, shared_task
from django.conf import settings

from .services import TelegramSenderService

service = TelegramSenderService(telegram_token=settings.VALENTINE_BOT_API_KEY)
DELAY_RETRY = 60


@shared_task(bind=True, max_retries=1, default_retry_delay=DELAY_RETRY)
def send_message_to_user(
    self: Task,  # type: ignore[type-arg]
    chat_id: str,
    message: str,
) -> None:
    try:
        service.send_message(chat_id=chat_id, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
