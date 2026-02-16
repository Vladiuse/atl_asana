from typing import Any

from message_sender.models import ScheduledMessage
from message_sender.serializers import ScheduledMessageSerializer
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import Leave


class LeaveSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.CharField(max_length=30)
    employee = serializers.CharField(max_length=254)
    supervisor_tag = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField(max_length=30)
    messages = serializers.SerializerMethodField(read_only=True)

    def get_messages(self, obj: Leave) -> ReturnDict[Any, Any]:
        scheduled = ScheduledMessage.objects.filter(reference_id=f"leave-{obj.pk}")
        return ScheduledMessageSerializer(scheduled, many=True).data
