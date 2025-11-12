from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Webhook
from .services import AddNotExistWebhooks

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ["id", "webhook_id", "resource_name", "resource_type", "target", "description"]
    list_display_links = ["id", "webhook_id"]
    actions = ("add_new_webhooks",)

    @admin.action(description="Добавить новые вебхуки из асаны")
    def add_new_webhooks(self, request: HttpRequest, queryset: QuerySet) -> None:
        _ = queryset
        try:
            result = AddNotExistWebhooks(asana_api_client=asana_client).execute()
            self.message_user(request, f"Успешно: {result}")
        except AsanaApiClientError as error:
            self.message_user(request, f"Ошибка выполнения: {error}", level=messages.ERROR)
