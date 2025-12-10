from common import RequestsSender
from common.message_sender import MessageSender, UserTag
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from asana.repository import AsanaUserRepository
from asana.utils import get_asana_profile_url_by_id

from .models import AsanaWebhook, AsanaWebhookRequestData, AtlasUser, WebhookHandler

message_sender = MessageSender(request_sender=RequestsSender())
asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
asana_user_repository = AsanaUserRepository(api_client=asana_api_client)


@admin.register(AtlasUser)
class AtlasUserAdmin(admin.ModelAdmin):
    list_display = [
        "user_id",
        "membership_id",
        "email",
        "name",
        "avatar_preview",
        "position",
        "messenger_code",
        "asana_profile_link",
    ]
    list_display_links = ["email", "name"]
    list_filter = ["position"]
    search_fields = ["email", "name"]
    actions = ["send_test_sms_for_user", "update_asana_users"]

    @admin.display(description="Avatar")
    def avatar_preview(self, obj) -> str:
        if not obj.avatar_url:
            return ""
        return format_html(
            '<img src="{}" width="60" height="60" style="border-radius:50%; object-fit:cover;" />',
            obj.avatar_url,
        )

    @admin.display(description="Профиль")
    def asana_profile_link(self, obj) -> str:
        profile_link = get_asana_profile_url_by_id(profile_id=obj.membership_id)
        return format_html(
            '<a href="{}" target="_blank">Открыть</a>',
            profile_link,
        )

    @admin.action(description="Отправить тестовое смс в телеграм")
    def send_test_sms_for_user(self, request: HttpRequest, queryset: QuerySet) -> None:
        errors_send_user = []
        success_send_count = 0
        for asana_user in queryset:
            try:
                message = f"Test message for {asana_user.user_comment_mention}"
                message_sender.send_message_to_user(message=message, user_tags=[UserTag(asana_user.messenger_code)])
                success_send_count += 1
            except ValueError:
                errors_send_user.append(asana_user)
        for user in errors_send_user:
            message = f'Не удалось отправить тестовое смс для {user} по тегу "{user.messenger_code}"'
            self.message_user(request, message, level=messages.ERROR)
        self.message_user(request, f"Успешно отправлено {success_send_count} сообщений", level=messages.SUCCESS)

    @admin.action(description="Обновить пользователей асаны (глобальный)")
    def update_asana_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        _ = queryset
        try:
            result = asana_user_repository.update_all()
            self.message_user(request, f"Успешно, {result}", level=messages.SUCCESS)
        except AsanaApiClientError as error:
            self.message_user(request, f"Не удалось обновить пользователей: {error}", level=messages.ERROR)


@admin.register(WebhookHandler)
class WebhookHandlerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created")
    ordering = ("-created",)
    readonly_fields = ("name", "description")

    def has_add_permission(self, request: HttpRequest, obj: WebhookHandler | None = None) -> bool:  # noqa: ARG002
        return False

    def has_delete_permission(self, request: HttpRequest, obj: WebhookHandler | None = None) -> bool:  # noqa: ARG002
        return False


@admin.register(AsanaWebhook)
class AsanaWebhookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "resource_type",
        "resource_id",
        "resource_name",
        "secret",
        "handlers_list",
        "created",
    )
    list_filter = ("resource_type",)
    ordering = ("-created",)

    def get_queryset(self, request) -> QuerySet[AsanaWebhook]:
        qs = super().get_queryset(request)
        return qs.prefetch_related("handlers")

    @admin.display(description="handlers")
    def handlers_list(self, obj) -> str:
        return ", ".join(obj.handlers.values_list("name", flat=True))


@admin.register(AsanaWebhookRequestData)
class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "webhook",
        "status",
        "created",
    )
    list_filter = ("webhook", "status",)
    readonly_fields = ("headers", "payload", "additional_data", "created")
    ordering = ("-created",)
