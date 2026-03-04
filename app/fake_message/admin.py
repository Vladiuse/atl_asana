from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "tag",
        "status",
        "parse_mode",
        "send_at",
        "created_at",
        "short_text",
    )
    list_filter = (
        "status",
        "tag",
        "parse_mode",
    )

    search_fields = ("text", "tag")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Основная информация", {"fields": ("text", "tag", "parse_mode")}),
        ("Статус и время", {"fields": ("status", "send_at", "created_at")}),
    )

    @admin.display(description="Текст сообщения")
    def short_text(self, obj: Message) -> str:
        text_max_length = 50
        if len(obj.text) > text_max_length:
            return f"{obj.text[:text_max_length]}..."
        return obj.text
