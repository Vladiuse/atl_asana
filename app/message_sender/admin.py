from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from message_sender.client import AtlasMessageSender
from message_sender.services import UserService

from .models import AtlasUser

message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)


@admin.register(AtlasUser)
class AtlasUserAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "name",
        "username",
        "email",
        "role",
        "tag",
        "telegram",
    )
    search_fields = (
        "name",
        "username",
        "email",
        "tag",
        "telegram",
    )
    list_filter = ("role",)
    ordering = ("name",)
    actions = ("update_messenger_users",)

    @admin.action(description="Обновить пользователей")
    def update_messenger_users(self, request: HttpRequest, queryset: QuerySet[AtlasUser]) -> None:
        _ = queryset
        service = UserService(message_sender_client=message_sender)
        result = service.update_all_users()
        message = str(result)
        self.message_user(request, message, level=messages.ERROR)
