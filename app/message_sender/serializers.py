from typing import Any

from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import ScheduledMessage


class ScheduledMessageSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]

    class Meta:
        model = ScheduledMessage
        fields = ("pk", "status", "run_at", "user_tag", "handler", "text")
        read_only_fields = ("pk", "status")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user_tag = attrs.get("user_tag")
        handler = attrs.get("handler")
        filled_fields = [bool(user_tag), bool(handler)]
        if sum(filled_fields) != 1:
            raise ValidationError("Only one of the fields 'user_tag' or 'handler' must be filled.")
        return attrs
