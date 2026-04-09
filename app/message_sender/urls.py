from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()

app_name = "message_sender"

urlpatterns = [
    path("", views.api_root, name="api_root"),
    path("", include(router.urls)),
]