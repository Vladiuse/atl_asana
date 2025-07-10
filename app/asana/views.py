from django.conf import settings
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import AsanaWebhookRequestData
from .serializers import AsanaWebhookRequestDataSerializer

@api_view(http_method_names=["POST"])
def webhook(request, format=None):
    secret = request.headers.get("X-Hook-Secret")
    # if not secret:
    #     return Response(data={"error": '"X-Hook-Secret" header required'}, status=status.HTTP_400_BAD_REQUEST)
    AsanaWebhookRequestData.objects.create(
        headers=dict(request.headers),
        payload=dict(request.data),
    )
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