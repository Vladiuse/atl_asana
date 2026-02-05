from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("employee", views.CustomerView)

app_name = "valentine_day"

urlpatterns = [
    path("", views.index, name="index"),
    path("", include(router.urls)),
]
