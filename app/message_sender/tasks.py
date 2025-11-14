from celery import shared_task
from common import MessageSender, RequestsSender
from common.message_sender import UserTag

message_sender = MessageSender(request_sender=RequestsSender())


@shared_task(bind=True, max_retries=2, default_60=60)
def send_log_message_task(self, message: str) -> dict | None:
    try:
        message_sender.send_log_message(message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_60=60)
def send_message_to_user_task(self, user_tags: list[str], message: str) -> dict | None:
    try:
        user_tags = [UserTag(value) for value in user_tags]
        message_sender.send_message_to_user(user_tags=user_tags, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_60=60)
def send_message_task(self, handler: str, message: str) -> dict | None:
    try:
        message_sender.send_message(handler=handler, message=message)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
