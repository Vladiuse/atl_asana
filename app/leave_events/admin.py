from django.contrib import admin

from .models import Leave, SupervisorNotificationChat


@admin.register(Leave)
class LeaveNotificationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "employee",
        "telegram_login",
        "supervisor_tag",
        "type",
        "status",
        "start_date",
        "end_date",
        "created",
    )
    list_filter = ("type",)
    search_fields = ("employee", "supervisor_tag")
    ordering = ("-created",)
    date_hierarchy = "start_date"


@admin.register(SupervisorNotificationChat)
class SupervisorNotificationChatAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("supervisor", "chat", "created_at")
    autocomplete_fields = ("supervisor", )
