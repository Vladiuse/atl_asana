from celery import Task, shared_task
from django.conf import settings

from .models import Employee
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


@shared_task
def test_check_mail_notify() -> None:
    message = """
Твое сердечко выдержало сутки ожидания? Достойный результат!

Купидон наконец-то разобрал свой почтовый ящик и готов доставить тебе всё, что там накопилось.

Твои анонимные (и не очень) валентинки уже заждались! 💌
""".strip()
    for employee in Employee.objects.all().can_notify():  # type: ignore[attr-defined]
        send_message_to_user.delay(chat_id=employee.telegram_user_id, message=message)  # type: ignore[attr-defined]
