from common.auth import BearerAuthentication
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import AtlasUser, ScheduledMessage
from .serializers import ScheduledMessageSerializer


@api_view()
@permission_classes(permission_classes=[IsAuthenticated])
@authentication_classes(authentication_classes=[SessionAuthentication, BearerAuthentication])
def api_root(request: Request) -> Response:
    _ = request
    data = {
        "atlas_users_telegram_logins": reverse("message_sender:atlas_users_telegram_logins", request=request),
    }
    return Response(data)

@api_view()
@permission_classes(permission_classes=[IsAuthenticated])
@authentication_classes(authentication_classes=[SessionAuthentication, BearerAuthentication])
def atlas_users_telegram_logins(request: Request) -> Response:
    _ = request
    logins = AtlasUser.objects.exclude(telegram="").values_list("telegram", flat=True)
    data = {
        "logins": logins,
    }
    return Response(data=data)


class ScheduledMessageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    queryset = ScheduledMessage.objects.all()
    serializer_class = ScheduledMessageSerializer
