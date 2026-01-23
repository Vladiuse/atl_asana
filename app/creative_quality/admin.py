import logging

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Creative, CreativeAdaptation, CreativeGeoData, CreativeProjectSection, Task
from .services import CreativeProjectSectionService

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "task_id",
        "task_name",
        "status",
        "is_completed",
        "assignee_id",
        "bayer_code",
        "created",
        "url_display",
    )
    list_filter = ("status",)
    search_fields = ("task_id", "task_name", "assignee_id", "bayer_code")
    ordering = ("-created",)

    @admin.display(description="url")
    def url_display(self, obj: Task) -> str:
        if obj.url:
            return format_html('<a href="{}" target="_blank">url</a>', obj.url)
        return "-"


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "task",
        "status",
        "display_estimate_url",
        "need_rated_at",
        "gsheet_sent",
        "created",
    )
    list_filter = ("status",)
    search_fields = ("task__task_id", "task__task_name")
    ordering = ("-created",)

    @admin.display(description="Estimate url")
    def display_estimate_url(self, obj: Creative) -> str:
        return format_html('<a href="{}" target="_blank">url</a>', obj.get_estimate_url())


@admin.register(CreativeAdaptation)
class CreativeAdaptationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "name", "creative")
    list_select_related = ("creative",)
    search_fields = ("name", "creative__name")
    list_filter = ("creative",)


@admin.register(CreativeGeoData)
class CreativeGeoDataAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("creative_adaptation", "status", "country", "hook", "hold", "ctr", "short_comment", "created")
    ordering = ("creative_adaptation",)

    @admin.display(description="Comment")
    def short_comment(self, obj: CreativeGeoData) -> str:
        comment_max_length = 50
        if obj.comment and len(obj.comment) > comment_max_length:
            return obj.comment[:comment_max_length] + "..."
        return obj.comment


@admin.register(CreativeProjectSection)
class CreativeProjectSectionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("section_id", "section_name", "project_name", "created")
    search_fields = ("section_id", "section_name", "project_name")
    list_filter = ("project_name",)
    ordering = ("-created",)
    readonly_fields = ("section_name", "project_name")

    def save_model(
        self,
        request: HttpRequest,
        obj: CreativeProjectSection,
        form: forms.ModelForm,  # type: ignore[type-arg]
        change: bool,  # noqa: FBT001
    ) -> None:
        super().save_model(request, obj, form, change)
        service = CreativeProjectSectionService(asana_api_client=asana_client)
        try:
            service.update_additional_info(creative_project_section=obj)
        except AsanaApiClientError:
            self.message_user(
                request,
                message=f"Не удалось обновить данные по секции: {obj}",
                level=messages.ERROR,
            )

    @admin.action(description="Обновить доп. данные по секциям")
    def update_additional_section_data(self, request: HttpRequest, queryset: QuerySet[CreativeProjectSection]) -> None:
        service = CreativeProjectSectionService(asana_api_client=asana_client)
        success_updated = 0
        for section in queryset:
            try:
                service.update_additional_info(creative_project_section=section)
                success_updated += 1
            except AsanaApiClientError:
                self.message_user(
                    request,
                    message=f"Не удалось обновить данные по секции: {section}",
                    level=messages.ERROR,
                )
        self.message_user(request, message=f"Обновлено секций: {success_updated}")
