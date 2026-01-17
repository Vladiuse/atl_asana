from django.contrib import admin

from .models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("iso_code", "name")
    search_fields = ("name", "iso_code")
    ordering = ("name",)
