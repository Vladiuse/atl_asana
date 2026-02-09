from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
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


class ValentineImageView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = ValentineImage.objects.all()
    serializer_class = ValentineImageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class ValentineView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Valentine.objects.all()
    serializer_class = ValentineSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


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
