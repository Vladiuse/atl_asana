from asana.client import AsanaApiClient
from django.conf import settings
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import AsanaComment, AsanaProject, AsanaWebhookRequestData
from .use_cases import FetchCommentTaskUrls

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "secret"]
    list_display_links = ["name"]


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]


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
        use_case = FetchCommentTaskUrls(asana_api_client=asana_api_client)
        result = use_case.execute()
        self.message_user(request, message=str(result))


admin.site.register(AsanaProject, AsanaProjectAdmin)
admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
admin.site.register(AsanaComment, AsanaCommentAdmin)
