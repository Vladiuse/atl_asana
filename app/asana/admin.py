import json
from json.decoder import JSONDecodeError

from django.contrib import admin

from .models import AsanaProject, AsanaWebhookRequestData, CompletedTask


class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "complete_section_id", "secret", "table_url"]
    list_display_links = ["name"]


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]


class CompletedTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "task_id", "project__name", "is_send_in_table", "to_status", "created"]
    list_display_links = ["id", "task_id"]

    @admin.display(boolean=True, description="To")
    def to_status(self, obj) -> bool | None:
        try:
            data = json.loads(obj.response_text)
            return data.get("success")
        except JSONDecodeError:
            return None


admin.site.register(AsanaProject, AsanaProjectAdmin)
admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)
