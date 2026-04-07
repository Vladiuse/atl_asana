from typing import Any

from message_sender.models import AtlasUser, ScheduledMessage
from message_sender.serializers import ScheduledMessageSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import Leave, LeaveStatus, LeaveType, SupervisorNotificationChat


class LeaveSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.ChoiceField(choices=LeaveType.choices)
    employee = serializers.CharField(max_length=254)
    telegram_login = serializers.CharField(max_length=254)
    supervisor_tag = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.ChoiceField(choices=LeaveStatus.choices)
    messages = serializers.SerializerMethodField(read_only=True)

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        data = data.copy()
        for field in ["telegram_login", "supervisor_tag"]:
            if field in data:
                data[field] = data[field].removeprefix("@").lower()
        return super().to_internal_value(data)

    def get_messages(self, obj: Leave) -> ReturnDict[Any, Any]:
        scheduled = ScheduledMessage.objects.filter(reference_id=f"leave-{obj.pk}")
        return ScheduledMessageSerializer(scheduled, many=True).data

    def _validate_telegram_user(self, value: str, field_name: str) -> str:
        login = value
        if not AtlasUser.objects.filter(telegram__iexact=login).exists():
            raise ValidationError({field_name: f"Unknown telegram login: @{login}"})
        return login

    def validate_telegram_login(self, value: str) -> str:
        return self._validate_telegram_user(value, field_name="telegram_login")

    def validate_supervisor_tag(self, value: str) -> str:
        login = value
        self._validate_telegram_user(value, field_name="supervisor_tag")
        if not SupervisorNotificationChat.objects.filter(supervisor__telegram__iexact=login).exists():
            raise ValidationError({"supervisor_tag": f"Supervisor @{login} dont have chat to notify"})
        return value

