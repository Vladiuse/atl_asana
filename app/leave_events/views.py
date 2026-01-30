from common.auth import BearerAuthentication
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from message_sender.models import ScheduledMessage
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import LeaveNotification
from .serializers import LeaveNotificationDeleteSerializer, LeaveNotificationSerializer


class LeaveNotificationView(ModelViewSet):  # type: ignore[type-arg]
    queryset = LeaveNotification.objects.all()
    serializer_class = LeaveNotificationSerializer
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["delete"], url_path="delete-by-ref")
    def delete_by_ref(self, request: Request) -> Response:
        serializer = LeaveNotificationDeleteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(
            LeaveNotification,
            start_date=serializer.validated_data["start_date"],
            employee=serializer.validated_data["employee"],
        )
        if instance.is_can_be_deleted():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {
            "details": "Cant delete LeaveNotification",
        }
        return Response(status=status.HTTP_400_BAD_REQUEST, data=data)


def messages_list(request: HttpRequest) -> HttpResponse:
    messages = ScheduledMessage.objects.filter(reference_id__startswith="leave-").order_by("-run_at")
    content = {
        "messages": messages,
    }
    return render(request, "message_sender/message_list.html", content)
