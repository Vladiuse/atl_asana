from common import MessageSender, RequestsSender
from django.conf import settings
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import AsanaWebhookRequestData
from .serializers import AsanaWebhookRequestDataSerializer
from .usecase import ProcessAsanaWebhookUseCase

message_sender = MessageSender(request_sender=RequestsSender())


@api_view(http_method_names=["POST"])
def webhook(request, format=None):
    secret = request.headers.get("X-Hook-Secret")
    asana_webhook = AsanaWebhookRequestData.objects.create(
        headers=dict(request.headers),
        payload=dict(request.data),
    )
    try:
        usecase = ProcessAsanaWebhookUseCase()
        usecase.execute(asana_webhook=asana_webhook)
    except Exception as error:
        message_sender.send_message(handler="kva_test", message=f"Error: {error}")
    data = {
        "success": True,
        "method": request.method,
        "headers": request.headers,
    }
    response = Response(data=data)
    response["X-Hook-Secret"] = settings.ASANA_HOOK_SECRET if settings.ASANA_HOOK_SECRET else secret
    return response


class AsanaWebhookRequestDataView(ModelViewSet):
    queryset = AsanaWebhookRequestData.objects.order_by("-pk")
    serializer_class = AsanaWebhookRequestDataSerializer

    @action(detail=True)
    def headers(self, request, pk):
        asana_webhook = self.get_object()
        return Response(data=asana_webhook.headers)

    @action(detail=True)
    def payload(self, request, pk):
        asana_webhook = self.get_object()
        return Response(data=asana_webhook.payload)
