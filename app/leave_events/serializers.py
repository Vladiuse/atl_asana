from rest_framework import serializers

from .models import LeaveType


class LeaveNotificationSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.ChoiceField(choices=LeaveType.choices)
    employee = serializers.CharField(max_length=254)
    supervisor_tag = serializers.CharField(max_length=254)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
