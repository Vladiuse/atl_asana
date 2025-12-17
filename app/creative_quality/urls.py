from django.urls import path

from . import views

app_name = "creative_quality"


urlpatterns = [
    path(
        "creative/<int:creative_pk>/mark_estimate/",
        views.CreativeMarkEstimateView.as_view(),
        name="creative_mark_estimate",
    ),
    path(
        "creative/<int:creative_id>/<str:task_id>/",
        views.CreativeDetailView.as_view(),
        name="creative_detail",
    ),
    path(
        "creative-geo-data/<int:geo_data_pk>/",
        views.CreativeGeoDataView.as_view(),
        name="creative_geo_data",
    ),
    path(
        "creative-geo-data/<int:creative_pk>/create-geo-data/",
        views.CreativeGeoDataCreateView.as_view(),
        name="creative_geo_data_create",
    ),
]
