from django.contrib import admin

from .models import AtlasUser


@admin.register(AtlasUser)
class AtlasUserAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "id",
        "name",
        "username",
        "email",
        "role",
        "tag",
        "telegram",
    )
    search_fields = (
        "name",
        "username",
        "email",
        "tag",
        "telegram",
    )
    list_filter = ("role",)
    ordering = ("name",)
