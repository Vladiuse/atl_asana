from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import ScheduledMessage
from .serializers import ScheduledMessageSerializer


@api_view()
@permission_classes(permission_classes=[IsAuthenticated])
@authentication_classes(authentication_classes=[SessionAuthentication, TokenAuthentication])
def api_root(request: Request) -> Response:
    _ = request
    data = {
        "13": "123",
    }
    return Response(data)





class ScheduledMessageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    queryset = ScheduledMessage.objects.all()
    serializer_class = ScheduledMessageSerializer
