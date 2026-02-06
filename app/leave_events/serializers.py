from datetime import timedelta
from typing import Any

from constance import config
from django.utils import timezone
from rest_framework import serializers

from .models import LeaveNotification


class LeaveNotificationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = LeaveNotification
        fields = (
            "type",
            "employee",
            "supervisor_tag",
            "start_date",
            "end_date",
        )

    def create(self, validated_data: dict[str, Any]) -> LeaveNotification:
        validated_data["cancellable_until"] = timezone.now() + timedelta(minutes=config.SEND_NOTIFICATION_DELAY)
        return super().create(validated_data)


class LeaveNotificationDeleteSerializer(serializers.Serializer):  # type: ignore[type-arg]
    employee = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
