import logging

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from asana.repository import AsanaUserRepository
from common import MessageSender, RequestsSender
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.text import Truncator

from comment_notifier.services import AsanaCommentNotifier, FetchCommentsAdditionalInfo

from .forms import ProjectIgnoredSectionForm
from .models import AsanaComment, AsanaWebhookProject, AsanaWebhookRequestData, ProjectIgnoredSection
from .services import LoadAdditionalInfoForProjectIgnoredSection, LoadAdditionalInfoForWebhookProject
from .tasks import fetch_comment_tasks_urls_task, fetch_missing_project_comments_task

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)

message_sender = MessageSender(request_sender=RequestsSender())
repository = AsanaUserRepository(api_client=asana_client)


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


@admin.register(ProjectIgnoredSection)
class ProjectIgnoredSectionAdmin(admin.ModelAdmin):
    list_display = ["project", "section_name", "section_id"]
    list_display_links = ["section_id", "section_name"]
    readonly_fields = ["section_name"]
    actions = ["update_additional_section_data"]
    form = ProjectIgnoredSectionForm

    def save_model(
        self,
        request: HttpRequest,
        obj: ProjectIgnoredSection,
        form: ProjectIgnoredSectionForm,
        change: bool,
    ) -> None:
        super().save_model(request, obj, form, change)
        service = LoadAdditionalInfoForProjectIgnoredSection(asana_api_client=asana_client)
        try:
            service.load(project_ignored_section=obj)
        except AsanaApiClientError:
            self.message_user(
                request,
                message=f"Не удаллось обновить данные по секции: {obj}",
                level=messages.ERROR,
            )

    @admin.action(description="Обновить доп. данные по секциям")
    def update_additional_section_data(self, request: HttpRequest, queryset: QuerySet) -> None:
        service = LoadAdditionalInfoForProjectIgnoredSection(asana_api_client=asana_client)
        success_updated = 0
        for section in queryset:
            try:
                service.load(project_ignored_section=section)
                success_updated += 1
            except AsanaApiClientError:
                self.message_user(
                    request,
                    message=f"Не удаллось обновить данные по секции: {section}",
                    level=messages.ERROR,
                )
        self.message_user(request, message=f"Обновленно секций: {success_updated}")


@admin.register(AsanaWebhookRequestData)
class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]


@admin.register(AsanaComment)
class AsanaCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "task_id",
        "comment_id",
        "project",
        "has_mention",
        "is_notified",
        "task_url_short",
        "is_deleted",
        "short_text",
        "created",
    )
    list_filter = ("has_mention", "is_notified", "is_deleted", "project")
    ordering = ("-created",)
    search_fields = ("user_id", "task_id", "comment_id")
    actions = (
        "fetch_task_urls",
        "fetch_missing_project_comments",
        "mark_as_not_notified",
        "mark_as_not_processed",
        "process_comment_and_notify",
        "update_additional_comment_data",
    )

    @admin.display(description="Task URL")
    def task_url_short(self, obj: AsanaComment) -> str:
        if obj.task_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.task_url, "Открыть")
        return "—"

    @admin.action(description="Создать ссылки на таски (глобальный)")
    def fetch_task_urls(self, request: HttpRequest, queryset: QuerySet) -> None:
        _ = queryset
        result = fetch_comment_tasks_urls_task.delay()
        self.message_user(request, message=f"Таск запущен: {result.id}")

    @admin.action(description="Найти пропущеные в проекте коментари (глобальный)")
    def fetch_missing_project_comments(self, request: HttpRequest, queryset: QuerySet) -> None:
        _ = queryset
        result = fetch_missing_project_comments_task.delay()
        self.message_user(request, message=f"Таск запущен: {result.id}")

    @admin.action(description="Пометить как не отправленные")
    def mark_as_not_notified(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(has_mention=False, is_notified=False)
        self.message_user(request, message=f"{queryset.count()} коментарив помечены как не отправление")

    @admin.action(description="Пометить как необработанный")
    def mark_as_not_processed(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(has_mention=None, is_notified=None, is_deleted=False)
        self.message_user(request, message=f"{queryset.count()} комментариев помечены как необработанные")

    @admin.action(description="Обработать комментарий и оповестить")
    def process_comment_and_notify(self, request: HttpRequest, queryset: QuerySet) -> None:
        if queryset.exclude(is_notified=None).count() != 0:
            self.message_user(
                request,
                message="Выбранные коментарии должны быть необработаными",
                level=messages.WARNING,
            )
            return
        success_processed_comments = 0
        notifier = AsanaCommentNotifier(
            asana_api_client=asana_client,
            message_sender=message_sender,
        )
        for comment in queryset:
            try:
                notifier.process(comment_id=comment.comment_id)
                success_processed_comments += 1
            except AsanaApiClientError:
                self.message_user(
                    request,
                    message=f"Коментарий {comment.comment_id} не удалось обработать",
                    level=messages.ERROR,
                )
        self.message_user(request, message=f"Успешно обработано коментариев: {success_processed_comments}")

    @admin.display(description="Text")
    def short_text(self, obj: AsanaComment) -> str:
        return Truncator(obj.text).chars(200)

    @admin.action(description="Обновить ссылку на таск коммента и текст")
    def update_additional_comment_data(self, request: HttpRequest, queryset: QuerySet) -> None:
        fetch_additional_comments_data_use_case = FetchCommentsAdditionalInfo(
            asana_api_client=asana_client,
        )
        result = fetch_additional_comments_data_use_case.execute(queryset=queryset)
        self.message_user(request, message=f"Результат {result}")
