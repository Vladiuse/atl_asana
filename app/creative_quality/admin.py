from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import AsanaWebhookProject, AsanaWebhookRequestData
from .services import LoadAdditionalInfoForWebhookProject

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


@admin.register(AsanaWebhookProject)
class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "secret", "project_name", "project_url_short"]
    list_display_links = ["name"]
    actions = ["update_project_data"]

    def save_model(
        self,
        request: HttpRequest,
        obj: AsanaWebhookProject,
        form: forms.ModelForm,
        change: bool,
    ) -> None:
        super().save_model(request, obj, form, change)
        service = LoadAdditionalInfoForWebhookProject(asana_api_client=asana_client)
        try:
            service.load(webhook_project=obj)
        except AsanaApiClientError:
            self.message_user(
                request,
                message=f"Не удаллось обновить проект: {obj}",
                level=messages.ERROR,
            )

    @admin.display(description="Task URL")
    def project_url_short(self, obj: AsanaWebhookProject) -> str:
        if obj.project_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.project_url, "Открыть")
        return "—"

    @admin.action(description="Обновить данные по проекту")
    def update_project_data(self, request: HttpRequest, queryset: QuerySet) -> None:
        service = LoadAdditionalInfoForWebhookProject(asana_api_client=asana_client)
        for webhook_project in queryset:
            try:
                service.load(webhook_project=webhook_project)
            except AsanaApiClientError:
                self.message_user(
                    request,
                    message=f"Не удаллось обновить проект: {webhook_project}",
                    level=messages.ERROR,
                )
        self.message_user(request, message="Данные обновлены")


@admin.register(AsanaWebhookRequestData)
class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]
    list_filter = [
        "is_target_event",
        "project__name",
    ]
