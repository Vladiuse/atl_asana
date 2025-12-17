from asana.client import AsanaApiClient
from common import MessageSender, RequestsSender
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from creative_quality.models import Creative, CreativeGeoData, CreativeStatus

from .forms import CreativeGeoDataForm
from .services import CreativeService

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


class CreativeDetailView(View):
    template_name = "creative_quality/creative/index.html"

    def get(self, request: HttpRequest, creative_id: int, task_id: str) -> HttpResponse:
        creative = get_object_or_404(Creative, pk=creative_id, task__task_id=task_id)
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
        return redirect("creative_quality:creative_detail", creative_id=creative.pk, task_id=creative.task.task_id)


class CreativeGeoDataView(View):
    template_name = "creative_quality/creative_geo_data/index.html"

    def get(self, request: HttpRequest, geo_data_pk: int) -> HttpResponse:
        creative_geo_data = get_object_or_404(CreativeGeoData, pk=geo_data_pk)
        form = CreativeGeoDataForm(instance=creative_geo_data, creative=creative_geo_data.creative)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "creative": creative_geo_data,
            },
        )

    def post(self, request: HttpRequest, geo_data_pk: int) -> HttpResponse:
        print("xxxx")
        geo_data = get_object_or_404(CreativeGeoData, pk=geo_data_pk)
        creative = geo_data.creative
        form = CreativeGeoDataForm(request.POST, creative=creative, instance=geo_data)
        if form.is_valid():
            geo_data = form.save(commit=False)
            geo_data.save()
            return redirect("creative_quality:creative_detail", creative_id=creative.pk, task_id=creative.task.task_id)
        context = {
            "form": form,
            "creative": creative,
        }
        return render(request, self.template_name, context)


class CreativeGeoDataCreateView(View):
    template_name = "creative_quality/creative_geo_data/index.html"

    def get(self, request: HttpRequest, creative_pk: int) -> HttpResponse:
        creative = get_object_or_404(Creative, pk=creative_pk)
        form = CreativeGeoDataForm(creative=creative)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "creative": creative,
            },
        )

    def post(self, request: HttpRequest, creative_pk: int) -> HttpResponse:
        creative = get_object_or_404(Creative, pk=creative_pk)
        form = CreativeGeoDataForm(request.POST, creative=creative)
        if form.is_valid():
            geo_data = form.save(commit=False)
            geo_data.creative = creative
            geo_data.save()
            return redirect("creative_quality:creative_detail", creative_id=creative.pk, task_id=creative.task.task_id)
        context = {
            "form": form,
            "creative": creative,
        }
        return render(request, self.template_name, context)
