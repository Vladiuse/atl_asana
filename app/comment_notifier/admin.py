from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import AsanaComment, AsanaProject, AsanaWebhookRequestData
from .tasks import fetch_comment_tasks_urls_task


@admin.register(AsanaProject)
class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "secret"]
    list_display_links = ["name"]


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
        "has_mention",
        "is_notified",
        "task_url_short",
        "is_deleted",
        "created",
    )
    list_filter = ("has_mention", "is_notified", "is_deleted")
    ordering = ("-created",)
    search_fields = ("user_id", "task_id", "comment_id")
    actions = ("fetch_task_urls",)

    @admin.display(description="Task URL")
    def task_url_short(self, obj: AsanaComment) -> str:
        if obj.task_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.task_url, "Открыть")
        return "—"

    @admin.action(description="Создать ссылки на таски")
    def fetch_task_urls(self, request: HttpRequest, queryset: QuerySet) -> None:
        _ = queryset
        result = fetch_comment_tasks_urls_task.delay()
        self.message_user(request, message=f"Таск запущен: {result.id}")
