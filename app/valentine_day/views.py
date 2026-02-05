from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rest_framework import viewsets

from .models import Employee
from .serializers import CustomerSerializer


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "valentine_day/index.html")


class CustomerView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Employee.objects.all()
    serializer_class = CustomerSerializer
