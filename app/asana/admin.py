from django.contrib import admin
from .models import AsanaWebhookRequestData, CompletedTask


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "created"]
    list_display_links = ["id", "__str__"]

class CompletedTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "task_id", "created"]
    list_display_links = ["id", "task_id"]


admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)