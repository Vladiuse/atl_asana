from django.contrib import admin
from .models import AsanaWebhookRequestData


class AsanaWebhookRequestDataAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "created"]
    list_display_links = ["id", "__str__"]


admin.site.register(AsanaWebhookRequestData, AsanaWebhookRequestDataAdmin)
