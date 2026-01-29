from django.contrib import admin

from .models import LeaveNotification


@admin.register(LeaveNotification)
class LeaveNotificationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "employee",
        "type",
        "start_date",
        "end_date",
        "cancellable_until",
        "created",
    )
    list_filter = ("type",)
    search_fields = ("employee", "supervisor_tag")
    ordering = ("-created",)
    date_hierarchy = "start_date"
