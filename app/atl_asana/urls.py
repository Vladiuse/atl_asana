from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("vga_lands/", include("vga_lands.urls")),
    path("comment_notifier/", include("comment_notifier.urls")),
]
