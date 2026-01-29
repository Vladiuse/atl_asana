from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("vga_lands/", include("vga_lands.urls")),
    path("asana/", include("asana.urls")),
    path("comment_notifier/", include("comment_notifier.urls")),
    path("creative-quality/", include("creative_quality.urls")),
    path("leave-events/", include("leave_events.urls")),
]
