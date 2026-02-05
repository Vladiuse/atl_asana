from django.contrib import admin
from django.utils.html import format_html

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "name", "surname", "position", "image_tag")

    @admin.display(description="Img")
    def image_tag(self, obj: Customer) -> str:
        if obj.image:
            return format_html('<img src="{}" style="height:50px;"/>', obj.image.url)
        return "-"
