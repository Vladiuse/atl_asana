from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("messages", views.MessageView)


app_name = "fake_message"

urlpatterns = [
    path("", views.api_root, name="api_root"),
    path("message-meta-data", views.message_meta_data, name="message_meta_data"),
    path("", include(router.urls)),
]
