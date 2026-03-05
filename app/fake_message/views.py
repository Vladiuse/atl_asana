from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import Message
from .serializers import MessageSerializer


class MessageView(viewsets.ModelViewSet):  # type: ignore[type-arg]
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("status", "tag")
