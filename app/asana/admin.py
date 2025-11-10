from django.contrib import admin
from django.utils.html import format_html

from .models import AtlasUser


class AtlasUserAdmin(admin.ModelAdmin):
    list_display = ["user_id", "membership_id", "email", "name", "avatar_preview", "position", "messenger_code"]

    def avatar_preview(self, obj) -> str:
        if not obj.avatar_url:
            return ""
        return format_html(
            '<img src="{}" width="60" height="60" style="border-radius:50%; object-fit:cover;" />',
            obj.avatar_url,
        )

    avatar_preview.short_description = "Avatar"


admin.site.register(AtlasUser, AtlasUserAdmin)
