from django.contrib import admin

from .models import AsanaProject, AsanaWebhookRequestData


class AsanaProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "secret"]
    list_display_links = ["name"]


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "is_target_event", "project__name", "created"]
    list_display_links = ["id", "__str__"]


admin.site.register(AsanaProject, AsanaProjectAdmin)
admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
