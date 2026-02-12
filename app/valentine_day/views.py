import io
import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from constance import config
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware
from PIL import Image
from pillow_heif import register_heif_opener
from rest_framework import status, viewsets
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
        return Valentine.objects.filter(sender=employee).order_by("-created")

    def perform_create(self, serializer: BaseSerializer[Valentine]) -> None:
        user: User = self.request.user  # type: ignore[assignment]
        employee = get_object_or_404(Employee, user=user)
        serializer.save(sender=employee)

    @action(detail=False, methods=["get"], url_path="received")
    def received_valentines(self, request: Request) -> Response:
        employee = get_object_or_404(Employee, user=request.user)
        qs = Valentine.objects.filter(recipient=employee).order_by("-created")
        serializer = self.get_serializer(qs, many=True)
        now = timezone.localtime(timezone.now())
        release_time = config.SHOW_VALENTINES_AT
        if release_time and is_naive(release_time):
            user_tz = ZoneInfo("Europe/Moscow")
            release_time = make_aware(release_time, user_tz)
        data = {
            "valentines": serializer.data,
            "is_up_time": now >= release_time if release_time else False,
        }
        return Response(data)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request: Request, pk: int) -> Response:
        _ = request
        valentine = Valentine.objects.get(pk=pk)
        valentine.is_read_by_recipient = True
        valentine.save(update_fields=["is_read_by_recipient"])
        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)


class GetTokenView(APIView):
    def get(self, request: Request) -> Response:
        serializer = GetTokenSerializers(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        telegram_login = serializer.validated_data["telegram_login"]
        employee = get_object_or_404(Employee, Q(telegram_user_id=telegram_user_id) | Q(telegram_login=telegram_login))
        token = Token.objects.get(user=employee.user)
        data = {
            "token": token.key,
            "employee_id": employee.pk,
            "user_id": employee.user.pk,
            "allow_send_valentines": config.ALLOW_SENDING_VALENTINES,
        }
        if employee.is_open_app is False:
            employee.is_open_app = True
            employee.sub_1 = telegram_user_id
            employee.save()
        return Response(data=data)


register_heif_opener()


class ValentineImageUploadView(APIView):
    def post(self, request: Request) -> Response:
        image_file = request.FILES.get("image")
        if image_file and image_file.name.lower().endswith(".heic"):
            img = Image.open(image_file)
            output = io.BytesIO()
            img.convert("RGB").save(output, format="JPEG", quality=90)
            new_name = image_file.name.lower().replace(".heic", ".jpg")
            request.data["image"] = ContentFile(output.getvalue(), name=new_name)
        serializer = ValentineImageSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
