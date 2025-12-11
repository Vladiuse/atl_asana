from django.urls import path

from . import views

app_name = "creative_quality"


urlpatterns = [
    path(
        "estimate-creative/<int:creative_id>/<str:task_id>/",
        views.CreativeUpdateView.as_view(),
        name="update-creative",
    ),
    path(
        "creative/<int:creative_id>/<str:task_id>/",
         views.CreativeDetailView.as_view(),
        name="creative_detail",
    ),
]
