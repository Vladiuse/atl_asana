from django.contrib import admin
from django.utils.html import format_html

from .models import Employee, Valentine, ValentineImage


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "telegram_user_id", "user", "name", "surname", "position", "image_tag")
    readonly_fields = ("user",)

    @admin.display(description="Img")
    def image_tag(self, obj: Employee) -> str:
        if obj.avatar:
            return format_html('<img src="{}" style="height:60px;"/>', obj.avatar.url)
        return "-"


@admin.register(ValentineImage)
class ValentineImageAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "owner", "image_tag", "created")
    list_filter = ("owner", "created")
    search_fields = ("owner__full_name",)
    readonly_fields = ("created",)

    @admin.display(description="Img")
    def image_tag(self, obj: ValentineImage) -> str:
        if obj.image:
            return format_html('<img src="{}" style="height:60px;"/>', obj.image.url)
        return "-"


@admin.register(Valentine)
class ValentineAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "sender",
        "recipient",
        "image_tag",
        "is_anonymously",
        "is_read_by_recipient",
        "created",
    )
    list_filter = ("recipient",)
    search_fields = (
        "sender__full_name",
        "recipient__full_name",
    )
    readonly_fields = ("created",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sender",
                    "recipient",
                    "image",
                    "text",
                    "is_read_by_recipient",
                ),
            },
        ),
        (
            "Анонимность",
            {
                "fields": (
                    "is_anonymously",
                    "anonymous_signature",
                ),
            },
        ),
        (
            "Системные поля",
            {
                "fields": ("created",),
            },
        ),
    )

    @admin.display(description="Img")
    def image_tag(self, obj: Valentine) -> str:
        if obj.image.image:
            return format_html('<img src="{}" style="height:60px;"/>', obj.image.image.url)
        return "-"
