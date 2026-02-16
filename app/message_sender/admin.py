from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from message_sender.client import AtlasMessageSender
from message_sender.services import UserService

from .models import AtlasUser, ScheduledMessage, ScheduledMessageStatus
from .services import MessageSenderService

message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)

message_service = MessageSenderService(message_sender=message_sender)


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


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "status",
        "run_at",
        "user_tag",
        "handler",
        "text_preview",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("user_tag", "handler", "text")
    ordering = ("-run_at",)
    readonly_fields = ("created_at",)
    actions = ("send_message", "mark_as_pending")

    fieldsets = (
        (
            None,
            {
                "fields": ("status", "run_at", "text"),
            },
        ),
        (
            "Target",
            {
                "fields": ("user_tag", "handler"),
            },
        ),
        (
            "Meta",
            {
                "fields": ("created_at",),
            },
        ),
    )

    @admin.action(description="Send message")
    def send_message(self, request: HttpRequest, queryset: QuerySet[ScheduledMessage]) -> None:
        for message in queryset:
            message_service.send(message=message)
        messages.success(request, f"{queryset.count()} сообщений отправлено")

    @admin.action(description="Mark pending")
    def mark_as_pending(self, request: HttpRequest, queryset: QuerySet[ScheduledMessage]) -> None:
        queryset.update(status=ScheduledMessageStatus.PENDING.value)
        messages.success(request, f"{queryset.count()} сообщений обновлено")

    @admin.display(description="Text")
    def text_preview(self, obj: ScheduledMessage) -> str:
        return mark_safe(obj.text.replace("\n", "<br>"))  # noqa: S308
