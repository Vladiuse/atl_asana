from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("asana-webhooks", views.AsanaWebhookRequestDataView)


urlpatterns = [
    path("webhook/", views.webhook),
    path("", include(router.urls)),
]
