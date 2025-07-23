from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("asana-webhooks", views.AsanaWebhookRequestDataView)


urlpatterns = [
    path("webhook/<str:project_name>/", views.AsanaWebhookView.as_view()),
    path("", include(router.urls)),
]
