from django.contrib import admin
from django.utils.html import format_html

from asana.utils import get_asana_profile_url_by_id

from .models import AtlasUser


class AtlasUserAdmin(admin.ModelAdmin):
    list_display = [
        "user_id",
        "membership_id",
        "email",
        "name",
        "avatar_preview",
        "position",
        "messenger_code",
        "asana_profile_link",
    ]
    list_display_links = ["email", "name"]
    list_filter = ["position"]
    search_fields = ["email", "name"]

    @admin.display(description="Avatar")
    def avatar_preview(self, obj) -> str:
        if not obj.avatar_url:
            return ""
        return format_html(
            '<img src="{}" width="60" height="60" style="border-radius:50%; object-fit:cover;" />',
            obj.avatar_url,
        )

    @admin.display(description="Профиль")
    def asana_profile_link(self, obj) -> str:
        profile_link = get_asana_profile_url_by_id(profile_id=obj.membership_id)
        return format_html(
            '<a href="{}" target="_blank">Открыть</a>',
            profile_link,
        )


admin.site.register(AtlasUser, AtlasUserAdmin)
