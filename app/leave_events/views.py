from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from .models import LeaveNotification
from .serializers import LeaveNotificationSerializer
from .services import LeaveNotificationService


class LeaveNotificationView(ModelViewSet):  # type: ignore[type-arg]
    queryset = LeaveNotification.objects.all()
    serializer_class = LeaveNotificationSerializer

    def perform_create(
        self,
        serializer: BaseSerializer,  # type: ignore[type-arg]
    ) -> None:
        LeaveNotificationService().create_notifications(validated_data=serializer.validated_data)
