from django.urls import path

from . import views

urlpatterns = [
    path("webhook/<str:webhook_name_name>/", views.AsanaWebhookView.as_view()),
]
