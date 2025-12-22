from celery import Task, shared_task
from common import MessageSender, RequestsSender
from common.message_sender import UserTag

message_sender = MessageSender(request_sender=RequestsSender())
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
        tags = [UserTag(value) for value in user_tags]
        message_sender.send_message_to_user(user_tags=tags, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=DELAY_RETRY)
def send_message_task(self: Task, handler: str, message: str) -> None:
    try:
        message_sender.send_message(handler=handler, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
