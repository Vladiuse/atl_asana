from django.db import transaction

from .client import AtlasMessageSender, Handlers
from .client.exceptions import AtlasMessageSenderError
from .models import AtlasUser, ScheduledMessage, ScheduledMessageStatus


class UserService:
    def __init__(self, message_sender_client: AtlasMessageSender):
        self.message_sender_client = message_sender_client

    def update_all_users(self) -> dict[str, int]:
        users = self.message_sender_client.users()
        created_count = 0
        telegrams = [user.telegram for user in users]
        with transaction.atomic():
            deleted_count, deleted_details = AtlasUser.objects.exclude(telegram__in=telegrams).delete()
            for user in users:
                obj, created = AtlasUser.objects.update_or_create(
                    telegram=user.telegram,
                    defaults={
                        "name": user.name,
                        "email": user.email or "",
                        "role": user.role,
                        "tag": user.tag,
                        "username": user.username,
                    },
                )
                if created:
                    created_count += 1
        return {"created_count": created_count, "deleted_count": deleted_count}


class MessageSenderService:
    def __init__(self, message_sender: AtlasMessageSender):
        self.message_sender = message_sender

    def send(self, message: ScheduledMessage) -> None:
        try:
            if message.handler:
                handler = Handlers(message.handler)
                self.message_sender.send_message(handler=handler, message=message.text, html=True)
            else:
                self.message_sender.send_message_to_user(user_tag=message.user_tag, message=message.text)
            message.status = ScheduledMessageStatus.SENT
        except (ValueError, AtlasMessageSenderError):
            message.status = ScheduledMessageStatus.FAILED
            raise
        finally:
            message.save()
