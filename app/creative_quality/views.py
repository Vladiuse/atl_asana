from asana.client import AsanaApiClient
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from creative_quality.models import Creative, CreativeAdaptation, CreativeGeoData, CreativeStatus

from .forms import CreativeGeoDataForm
from .services import CreativeService

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


class CreativeDetailView(View):
    template_name = "creative_quality/creative/index.html"

    def get(self, request: HttpRequest, creative_pk: int, task_id: str) -> HttpResponse:
        creative = get_object_or_404(
            Creative.objects.prefetch_related("adaptations", "adaptations__geo_data"),
            pk=creative_pk,
            task__task_id=task_id,
        )
        return render(
            request,
            self.template_name,
            {
                "creative": creative,
                "creative_statuses": CreativeStatus,
            },
        )


class CreativeMarkEstimateView(View):
    def post(self, request: HttpRequest, creative_pk: int) -> HttpResponse:
        _ = request
        creative = get_object_or_404(Creative, pk=creative_pk)
        creative_service = CreativeService(asana_api_client=asana_api_client)
        creative_service.end_estimate(creative=creative)
        return redirect("creative_quality:creative_detail", creative_pk=creative.pk, task_id=creative.task.task_id)


class CreativeGeoDataDetailView(View):
    template_name = "creative_quality/creative_geo_data/index.html"

    def get(self, request: HttpRequest, geo_data_pk: int) -> HttpResponse:
        creative_geo_data = get_object_or_404(CreativeGeoData, pk=geo_data_pk)
        form = CreativeGeoDataForm(
            instance=creative_geo_data, creative_adaptation=creative_geo_data.creative_adaptation
        )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "creative_geo_data": creative_geo_data,
                "creative": creative_geo_data.creative_adaptation,
            },
        )

    def post(self, request: HttpRequest, geo_data_pk: int) -> HttpResponse:
        creative_geo_data = get_object_or_404(CreativeGeoData, pk=geo_data_pk)
        creative_adaptation = creative_geo_data.creative_adaptation
        form = CreativeGeoDataForm(request.POST, creative_adaptation=creative_adaptation, instance=creative_geo_data)
        if form.is_valid():
            creative_geo_data = form.save(commit=False)
            creative_geo_data.save()
            return redirect(
                "creative_quality:creative_detail",
                creative_pk=creative_adaptation.creative.pk,
                task_id=creative_adaptation.creative.task.task_id,
            )
        context = {
            "form": form,
            "creative_geo_data": creative_geo_data,
        }
        return render(request, self.template_name, context)


class CreativeGeoDataCreateView(View):
    template_name = "creative_quality/creative_geo_data/index.html"

    def get(self, request: HttpRequest, creative_adaptation_pk: int) -> HttpResponse:
        creative_adaptation = get_object_or_404(CreativeAdaptation, pk=creative_adaptation_pk)
        form = CreativeGeoDataForm(creative_adaptation=creative_adaptation)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "creative_adaptation": creative_adaptation,
            },
        )

    def post(self, request: HttpRequest, creative_adaptation_pk: int) -> HttpResponse:
        creative_adaptation = get_object_or_404(CreativeAdaptation, pk=creative_adaptation_pk)
        form = CreativeGeoDataForm(request.POST, creative_adaptation=creative_adaptation)
        if form.is_valid():
            geo_data = form.save(commit=False)
            geo_data.creative_adaptation = creative_adaptation
            geo_data.save()
            return redirect(
                "creative_quality:creative_detail",
                creative_pk=creative_adaptation.creative.pk,
                task_id=creative_adaptation.creative.task.task_id,
            )
        context = {
            "form": form,
            "creative_adaptation": creative_adaptation,
        }
        return render(request, self.template_name, context)


class CreativeGeoDataDeleteView(View):
    def post(self, request: HttpRequest, geo_data_pk: int) -> HttpResponse:
        _ = request
        geo_data = get_object_or_404(CreativeGeoData, pk=geo_data_pk)
        creative = geo_data.creative_adaptation.creative
        geo_data.delete()
        return redirect("creative_quality:creative_detail", creative_pk=creative.pk, task_id=creative.task.task_id)
