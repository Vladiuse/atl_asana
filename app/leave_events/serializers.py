from typing import Any

from message_sender.models import AtlasUser, ScheduledMessage
from message_sender.serializers import ScheduledMessageSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import Leave, LeaveStatus, LeaveType


class LeaveSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.ChoiceField(choices=LeaveType.choices)
    employee = serializers.CharField(max_length=254)
    telegram_login = serializers.CharField(max_length=254)
    supervisor_tag = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.ChoiceField(choices=LeaveStatus.choices)
    messages = serializers.SerializerMethodField(read_only=True)

    def get_messages(self, obj: Leave) -> ReturnDict[Any, Any]:
        scheduled = ScheduledMessage.objects.filter(reference_id=f"leave-{obj.pk}")
        return ScheduledMessageSerializer(scheduled, many=True).data

    def validate_telegram_login(self, value: str) -> str:
        value = value.removeprefix("@")
        if not AtlasUser.objects.filter(telegram=value).exists():
            raise ValidationError({"telegram_login": f"Unknown telegram login: @{value}"})
        return value
