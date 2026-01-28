from rest_framework import mixins, viewsets

from .models import ScheduledMessage
from .serializers import ScheduledMessageSerializer


class ScheduledMessageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    queryset = ScheduledMessage.objects.all()
    serializer_class = ScheduledMessageSerializer
