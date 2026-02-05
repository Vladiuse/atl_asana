from rest_framework import serializers

from .models import Employee


class CustomerSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]

    class Meta:
        model = Employee
        fields = "__all__"

