from django.contrib import admin

from .models import Leave


@admin.register(Leave)
class LeaveNotificationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "employee",
        "type",
        "start_date",
        "end_date",
        "created",
    )
    list_filter = ("type",)
    search_fields = ("employee", "supervisor_tag")
    ordering = ("-created",)
    date_hierarchy = "start_date"
