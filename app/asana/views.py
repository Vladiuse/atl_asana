from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AsanaWebhookRequestData


@api_view(http_method_names=["GET", "POST"])
def webhook(request, format=None):
    # secret = request.headers.get("X-Hook-Secret")
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
    response["X-Hook-Secret"] = settings.ASANA_HOOK_SECRET
    return response
