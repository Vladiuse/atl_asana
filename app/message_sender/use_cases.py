from message_sender.client.exceptions import AtlasMessageSenderError

from .models import ScheduledMessage
from .services import MessageSenderService


class SendScheduledMessagesUseCase:
    ERROR_TEMPLATE = "🔴 {cls}\nmessage_id: {message_id}\nError: {error}"

    def __init__(self, sender_service: MessageSenderService):
        self.sender_service = sender_service

    def execute(self) -> None:
        from .tasks import send_log_message_task

        for message in ScheduledMessage.objects.need_send():
            try:
                self.sender_service.send(message)
            except (TypeError, AtlasMessageSenderError) as error:
                error_message = self.ERROR_TEMPLATE.format(
                    cls=self.__class__.__name__,
                    message_id=message.pk,
                    error=error,
                )
                send_log_message_task.delay(message=error_message)  # type: ignore[attr-defined]
