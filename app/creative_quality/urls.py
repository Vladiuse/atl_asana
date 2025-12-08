from django.urls import path

from . import views

urlpatterns = [
    path("webhook/<str:project_name>/", views.AsanaWebhookView.as_view()),
]
