from asana.client import AsanaApiClient
from common import MessageSender, RequestsSender
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from creative_quality.models import Creative, CreativeStatus

from .forms import CreativeForm
from .services import CreativeEstimationData, CreativeService

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


class CreativeUpdateView(View):
    template_name = "creative_quality/creative/update.html"

    def get(self, request: HttpRequest, creative_id: int, task_id: str) -> HttpResponse:
        creative = get_object_or_404(Creative, pk=creative_id, task__task_id=task_id)
        form = CreativeForm(instance=creative)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "creative": creative,
            },
        )

    def post(self, request: HttpRequest, creative_id: int, task_id: str) -> HttpResponse:
        creative = get_object_or_404(Creative, pk=creative_id, task__task_id=task_id)
        form = CreativeForm(request.POST, instance=creative)
        if form.is_valid():
            estimate_data = CreativeEstimationData(
                hook=form.cleaned_data["hook"],
                hold=form.cleaned_data["hook"],
                ctr=form.cleaned_data["ctr"],
                comment=form.cleaned_data["comment"],
                need_complete_task=True,
            )
            estimate_service = CreativeService(asan_api_client=asana_api_client)
            estimate_service.estimate(creative=creative, estimate_data=estimate_data)
            return redirect("creative_quality:creative_detail", creative_id=creative.pk, task_id=creative.task.task_id)

        return render(request, self.template_name, {"form": form, "creative": creative})


class CreativeDetailView(View):
    template_name = "creative_quality/creative/detail.html"

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
