from celery.signals import task_failure
from common import MessageSender, RequestsSender

message_sender = MessageSender(request_sender=RequestsSender())


@task_failure.connect
def notify_in_telegram(  # noqa: PLR0913
    sender=None,
    task_id=None,  # noqa: ARG001
    exception=None,
    args=None,  # noqa: ARG001
    kwargs=None,  # noqa: ARG001
    traceback=None,  # noqa: ARG001
    einfo=None,
    **kw,  # noqa: ARG001
) -> None:
    message = f"Task failed!\nTask id: {task_id}\nTask name: {sender.name}\nException: {exception}\nInfo: {einfo}\n"
    message_sender.send_log_message(message=message)
