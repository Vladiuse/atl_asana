from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from creative_quality.models import Creative, CreativeStatus

from .forms import CreativeForm


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
            creative_obj = form.save(commit=False)
            creative_obj.status = CreativeStatus.RATED
            creative_obj.save()
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
