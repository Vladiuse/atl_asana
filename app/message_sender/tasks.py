# mypy: disable-error-code=type-arg
from celery import Task, shared_task
from django.conf import settings

from message_sender.client import AtlasMessageSender, Handlers
from message_sender.services import MessageSenderService, UserService

from .use_cases import SendScheduledMessagesUseCase

message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)
sender_service = MessageSenderService(
    message_sender=message_sender,
)
DELAY_RETRY = 60


@shared_task(bind=True, max_retries=2, default_retry_delay=DELAY_RETRY)
def send_log_message_task(self: Task, message: str) -> None:
    try:
        message_sender.send_log_message(message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=DELAY_RETRY)
def send_message_to_user_task(self: Task, user_tags: list[str], message: str) -> None:
    try:
        message_sender.send_message_to_users(user_tags=user_tags, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=DELAY_RETRY)
def send_message_task(self: Task, handler: Handlers, message: str) -> None:
    try:
        message_sender.send_message(handler=handler, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task
def update_messenger_users() -> dict[str, int]:
    service = UserService(message_sender_client=message_sender)
    return service.update_all_users()


@shared_task()
def send_scheduled_messages_task() -> None:
    SendScheduledMessagesUseCase(sender_service=sender_service).execute()
