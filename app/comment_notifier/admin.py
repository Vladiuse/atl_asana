from django.contrib import admin

from .models import AsanaComment, AsanaProject, AsanaWebhookRequestData


class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "secret"]
    list_display_links = ["name"]


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]


class AsanaCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "task_id", "comment_id", "has_mention", "is_notified", "created")
    list_filter = ("has_mention", "is_notified")
    ordering = ("-created",)


admin.site.register(AsanaProject, AsanaProjectAdmin)
admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
admin.site.register(AsanaComment, AsanaCommentAdmin)
