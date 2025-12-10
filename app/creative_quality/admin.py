from django.contrib import admin
from .models import Task, Creative, CreativeProjectSection


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("task_id", "task_name", "status", "is_complete", "assignee_id", "bayer_code", "created")
    list_filter = ("status", "is_complete",)
    search_fields = ("task_id", "task_name", "assignee_id", "bayer_code")
    ordering = ("-created",)


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("task", "is_rated", "hook", "hold", "crt", "need_rated_at", "created")
    list_filter = ("is_rated", "need_rated_at",)
    search_fields = ("task__task_id", "task__task_name")
    ordering = ("-created",)


@admin.register(CreativeProjectSection)
class CreativeProjectSectionAdmin(admin.ModelAdmin):
    list_display = ("section_id", "section_name", "project_name", "created")
    search_fields = ("section_id", "section_name", "project_name")
    list_filter = ("project_name",)
    ordering = ("-created",)
