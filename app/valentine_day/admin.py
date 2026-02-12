from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Employee, Valentine, ValentineImage


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "telegram_user_id",
        "telegram_login",
        "user",
        "name",
        "surname",
        "position",
        "is_open_app",
        "send_count",
        "received_count",
        "image_tag",
        "can_receive_valentine",
        "sub_1",
    )
    readonly_fields = ("user",)
    list_filter = ("is_open_app",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Employee]:
        _ = request
        qs = super().get_queryset(request=request).prefetch_related("sent_valentines", "received_valentines")
        return qs.annotate(
            send_count=Count("sent_valentines", distinct=True),
            received=Count("received_valentines", distinct=True),
        )

    @admin.display(description="Отправил", ordering="send_count")
    def send_count(self, obj: Employee) -> int:
        return getattr(obj, "send_count", 0)

    @admin.display(description="Получил", ordering="received")
    def received_count(self, obj: Employee) -> int:
        return getattr(obj, "received", 0)

    @admin.display(description="Img")
    def image_tag(self, obj: Employee) -> str:
        if obj.avatar:
            return format_html('<img src="{}" style="height:80px;"/>', obj.avatar.url)
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
