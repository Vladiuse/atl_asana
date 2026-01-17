from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AsanaWebhook, AsanaWebhookRequestData
from .tasks import process_asana_webhook_task


class AsanaWebhookView(APIView):
    def post(self, request: Request, webhook_name: str, format: str | None = None) -> Response:
        _ = format
        webhook = get_object_or_404(AsanaWebhook, name=webhook_name)
        header_secret = request.headers.get("X-Hook-Secret")
        if header_secret and webhook.secret == "":
            return self.create_webhook_response(webhook=webhook, secret=header_secret)
        if webhook.secret == "":
            data = {
                "success": False,
                "message": f"Webhook {webhook.name} has no secret key!",
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        asana_webhook_data = AsanaWebhookRequestData.objects.create(
            headers=dict(request.headers),
            payload=dict(request.data),
            webhook=webhook,
        )
        process_asana_webhook_task.delay(asana_webhook_data_id=asana_webhook_data.pk)  # type: ignore[attr-defined]
        data = {
            "success": True,
            "method": request.method,
            "headers": request.headers,
        }
        response = Response(data=data)
        response["X-Hook-Secret"] = webhook.secret
        return response

    def create_webhook_response(self, webhook: AsanaWebhook, secret: str) -> Response:
        webhook.secret = secret
        webhook.save()
        data = {
            "status": True,
            "message": f"webhook created for project {webhook.name}",
        }
        response = Response(data=data, status=status.HTTP_201_CREATED)
        response["X-Hook-Secret"] = webhook.secret
        return response
