from django.urls import path

from . import views

app_name = "valentine_day"

urlpatterns = [
    path("", views.index, name="index"),
]
