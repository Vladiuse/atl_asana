from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Employee, Valentine, ValentineImage
from .serializers import CustomerSerializer, ValentineImageSerializer, ValentineSerializer


@api_view(["GET"])
def api_root(request: Request, format: str | None = None) -> Response:
    return Response(
        {
            "my-valentines": reverse("valentine_day:valentine-list", request=request, format=format),
            "my-images": reverse("valentine_day:valentine-image-list", request=request, format=format),
        },
    )


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "valentine_day/index.html")


class CustomerView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Employee.objects.all()
    serializer_class = CustomerSerializer


class ValentineImageView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = ValentineImage.objects.all()
    serializer_class = ValentineImageSerializer


class ValentineView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Valentine.objects.all()
    serializer_class = ValentineSerializer
