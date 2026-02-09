from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("employee", views.EmployeeView)
router.register("my-valentines", views.ValentineView)
router.register("my-images", views.ValentineImageView, basename="valentine-image")

app_name = "valentine_day"

urlpatterns = [
    path("", views.index, name="index"),
    path("api-root/", views.api_root, name="api_root"),
    path("get-token/", views.GetTokenView.as_view()),
    path("", include(router.urls)),
]
