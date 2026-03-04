from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("messages", views.MessageView)


app_name = "fake_message"

urlpatterns = [
    path("", include(router.urls)),
]
