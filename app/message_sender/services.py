from django.db import transaction

from .client import MessageSender
from .models import AtlasUser


class UserService:
    def __init__(self, message_sender_client: MessageSender):
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
