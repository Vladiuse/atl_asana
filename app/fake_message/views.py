from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Handlers, Message, MessageStatus, TgParseMode
from .serializers import MessageSerializer


@api_view(["GET"])
def api_root(request: Request) -> Response:
    data = {
        "message_meta_data": reverse("fake_message:message_meta_data", request=request),
        "messages": reverse("fake_message:message-list", request=request),
    }
    return Response(data)


@api_view(["GET"])
def message_meta_data(request: Request) -> Response:
    _ = request
    data = {
        "statuses": [{"value": status.value, "label": status.label} for status in MessageStatus],
        "parse_modes": [{"value": parse_mode.value, "label": parse_mode.label} for parse_mode in TgParseMode],
        "handlers": [{"value": handler.value, "label": handler.label} for handler in Handlers],
    }
    return Response(data)


class MessageView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("status", "tag")
