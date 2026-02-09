from typing import Any

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .models import Employee, Valentine, ValentineImage
from .serializers import CustomerSerializer, GetTokenSerializers, ValentineImageSerializer, ValentineSerializer


@api_view(["GET"])
def api_root(request: Request, format: str | None = None) -> Response:
    return Response(
        {
            "my-valentines": reverse("valentine_day:valentine-list", request=request, format=format),
            "my-images": reverse("valentine_day:valentine-image-list", request=request, format=format),
            "employee": reverse("valentine_day:employee-list", request=request, format=format),
        },
    )


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "valentine_day/index.html")


class EmployeeView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Employee.objects.all()
    serializer_class = CustomerSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet[Valentine]:
        user: User = self.request.user  # type: ignore[assignment]
        return super().get_queryset().exclude(user=user)

    @action(detail=False, methods=["get"], url_path="available-recipients")
    def available_recipients(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        employee = get_object_or_404(Employee, user=user)
        recipients_ids_have_valentines = list(
            Valentine.objects.filter(sender=employee).values_list("recipient_id", flat=True),
        )
        ids = list(
            self.get_queryset()
            .exclude(pk__in=[employee.pk, *recipients_ids_have_valentines])
            .values_list("id", flat=True),
        )
        return Response(ids)


class ValentineImageView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = ValentineImage.objects.all()
    serializer_class = ValentineImageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class ValentineView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = ValentineSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet[Valentine]:
        user: User = self.request.user  # type: ignore[assignment]
        employee = get_object_or_404(Employee, user=user)
        return Valentine.objects.filter(sender=employee)

    def perform_create(self, serializer: BaseSerializer[Valentine]) -> None:
        user: User = self.request.user  # type: ignore[assignment]
        employee = get_object_or_404(Employee, user=user)
        serializer.save(sender=employee)


class GetTokenView(APIView):
    def get(self, request: Request) -> Response:
        serializer = GetTokenSerializers(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        employee = get_object_or_404(Employee, telegram_user_id=telegram_user_id)
        token = Token.objects.get(user=employee.user)
        data = {
            "token": token.key,
        }
        return Response(data=data)
