from django.contrib import admin

from .models import OffboardingTask


@admin.register(OffboardingTask)
class OffboardingTaskAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "asana_task_id",
        "status",
        "notified_created_at",
        "notified_created",
        "notified_need_payroll",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("asana_task_id",)
    ordering = ("-created_at",)
