from rest_framework import serializers

from .models import AsanaWebhookRequestData


class AsanaWebhookRequestDataSerializer(serializers.HyperlinkedModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = AsanaWebhookRequestData
        exclude = ("headers",)
