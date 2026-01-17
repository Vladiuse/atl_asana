# ruff: noqa: PLR0913, ANN001, ANN003, ARG001
from celery.signals import task_failure
from django.conf import settings
from message_sender.client import MessageSender

message_sender = MessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)


@task_failure.connect  # type: ignore[misc]
def notify_in_telegram(  # type: ignore[no-untyped-def]
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kw,
) -> None:
    message = f"⚠️ Task failed!\nTask id: {task_id}\nTask name: {sender.name}\nException: {exception}\nInfo: {einfo}\n"
    message_sender.send_log_message(message=message)
