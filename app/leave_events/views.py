from common.auth import BearerAuthentication
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from message_sender.models import ScheduledMessage
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Leave
from .serializers import LeaveSerializer
from .services import LeaveNotificationService


class LeaveNotificationView(ModelViewSet):  # type: ignore[type-arg]
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    authentication_classes = (BearerAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["post"], url_path="process-by-status")
    def process_by_status(self, request: Request) -> Response:
        serializer = LeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = LeaveNotificationService()
        leave = service.process_google_data(leave_data=serializer.validated_data)
        serializer = LeaveSerializer(leave)
        return Response(data=serializer.data)


def messages_list(request: HttpRequest) -> HttpResponse:
    messages = ScheduledMessage.objects.filter(reference_id__startswith="leave-").order_by("-run_at")
    content = {
        "messages": messages,
    }
    return render(request, "message_sender/message_list.html", content)
