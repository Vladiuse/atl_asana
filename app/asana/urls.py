from django.urls import path

from . import views

app_name = "asana"

urlpatterns = [
    path("webhook/<str:webhook_name>/", views.AsanaWebhookView.as_view(), name="webhook"),
]
