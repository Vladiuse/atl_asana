# ruff: noqa: PLR0913, ANN001, ANN003, ARG001
from celery.signals import task_failure
from common import MessageSender, RequestsSender

message_sender = MessageSender(request_sender=RequestsSender())


@task_failure.connect  # type: ignore[misc]
def notify_in_telegram(  # type: ignore[type-arg, no-untyped-def]]
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
