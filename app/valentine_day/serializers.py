from typing import Any

from rest_framework import serializers

from .models import Employee, Valentine, ValentineImage


class CustomerSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Employee
        fields = "__all__"

    def to_representation(self, instance: Employee) -> dict[str, Any]:
        ret = super().to_representation(instance)
        if ret["avatar"]:
            ret["avatar"] = ret["avatar"].replace("http:", "").replace("https:", "")
        return ret


class ValentineImageSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = ValentineImage
        fields = "__all__"
        read_only_fields = ("created",)

    def to_representation(self, instance: ValentineImage) -> dict[str, Any]:
        ret = super().to_representation(instance)
        ret["image"] = ret["image"].replace("http:", "").replace("https:", "")
        return ret


class ValentineSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Valentine
        fields = "__all__"
        read_only_fields = ("sender", "created")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("is_anonymously") and not data.get("anonymous_signature"):
            raise serializers.ValidationError(
                "При анонимной отправке нужно указать подпись",
            )
        return data


class GetTokenSerializers(serializers.Serializer):  # type: ignore[type-arg]
    telegram_user_id = serializers.CharField()
