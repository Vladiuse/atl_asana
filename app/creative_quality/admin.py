import logging

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Creative, CreativeProjectSection, Task
from .services import LoadAdditionalInfoForCreativeProjectSection

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("task_id", "task_name", "status", "assignee_id", "bayer_code", "created", "url_display")
    list_filter = ("status",)
    search_fields = ("task_id", "task_name", "assignee_id", "bayer_code")
    ordering = ("-created",)

    @admin.display(description="url")
    def url_display(self, obj: Task) -> str:
        if obj.url:
            return format_html('<a href="{}" target="_blank">url</a>', obj.url)
        return "-"


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "status", "hook", "hold", "crt", "comment", "need_rated_at", "created")
    list_filter = ("status",)
    search_fields = ("task__task_id", "task__task_name")
    ordering = ("-created",)


@admin.register(CreativeProjectSection)
class CreativeProjectSectionAdmin(admin.ModelAdmin):
    list_display = ("section_id", "section_name", "project_name", "created")
    search_fields = ("section_id", "section_name", "project_name")
    list_filter = ("project_name",)
    ordering = ("-created",)
    readonly_fields = ("section_name", "project_name")

    def save_model(
        self,
        request: HttpRequest,
        obj: CreativeProjectSection,
        form: forms.ModelForm,
        change: bool,
    ) -> None:
        super().save_model(request, obj, form, change)
        service = LoadAdditionalInfoForCreativeProjectSection(asana_api_client=asana_client)
        try:
            service.load(creative_project_section=obj)
        except AsanaApiClientError:
            self.message_user(
                request,
                message=f"Не удаллось обновить данные по секции: {obj}",
                level=messages.ERROR,
            )

    @admin.action(description="Обновить доп. данные по секциям")
    def update_additional_section_data(self, request: HttpRequest, queryset: QuerySet) -> None:
        service = LoadAdditionalInfoForCreativeProjectSection(asana_api_client=asana_client)
        success_updated = 0
        for section in queryset:
            try:
                service.load(creative_project_section=section)
                success_updated += 1
            except AsanaApiClientError:
                self.message_user(
                    request,
                    message=f"Не удаллось обновить данные по секции: {section}",
                    level=messages.ERROR,
                )
        self.message_user(request, message=f"Обновленно секций: {success_updated}")
