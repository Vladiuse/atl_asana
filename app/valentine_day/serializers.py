from rest_framework import serializers

from .models import Employee, Valentine, ValentineImage


class CustomerSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Employee
        fields = "__all__"


class ValentineImageSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        models = ValentineImage
        fields = "__all__"


class ValentineSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Valentine
        fields = "__all__"
