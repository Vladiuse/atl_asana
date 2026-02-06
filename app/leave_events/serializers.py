from datetime import timedelta
from typing import Any

from constance import config
from django.utils import timezone
from message_sender.models import ScheduledMessage
from message_sender.serializers import ScheduledMessageSerializer
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import LeaveNotification


class LeaveNotificationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    messages = serializers.SerializerMethodField()

    class Meta:
        model = LeaveNotification
        fields = (
            "type",
            "employee",
            "supervisor_tag",
            "start_date",
            "end_date",
            "messages",
        )

    def create(self, validated_data: dict[str, Any]) -> LeaveNotification:
        validated_data["cancellable_until"] = timezone.now() + timedelta(minutes=config.SEND_NOTIFICATION_DELAY)
        return super().create(validated_data)

    def get_messages(self, obj: LeaveNotification) -> ReturnDict[Any, Any]:
        scheduled = ScheduledMessage.objects.filter(reference_id=f"leave-{obj.pk}")
        return ScheduledMessageSerializer(scheduled, many=True).data


class LeaveNotificationDeleteSerializer(serializers.Serializer):  # type: ignore[type-arg]
    employee = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
