from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()

app_name = "message_sender"

urlpatterns = [
    path("", views.api_root, name="api_root"),
    path("atlas-users-telegram-logins/", views.atlas_users_telegram_logins, name="atlas_users_telegram_logins"),
    path("", include(router.urls)),
]
