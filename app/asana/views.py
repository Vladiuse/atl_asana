from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import AsanaProject, AsanaWebhookRequestData
from .serializers import AsanaWebhookRequestDataSerializer
from .tasks import process_asana_webhook


class AsanaWebhookView(APIView):
    def post(self, request, project_name, format=None):
        project = get_object_or_404(AsanaProject, name=project_name)
        header_secret = request.headers.get("X-Hook-Secret")
        if header_secret and project.secret == "":
            return self.create_webhook_response(project=project, secret=header_secret)
        if project.secret == "":
            data = {
                "success": False,
                "message": f"Project {project.name} has no secret key!",
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        asana_webhook = AsanaWebhookRequestData.objects.create(
            headers=dict(request.headers),
            payload=dict(request.data),
            project=project,
        )
        process_asana_webhook.delay(asana_webhook_id=asana_webhook.pk)
        data = {
            "success": True,
            "method": request.method,
            "headers": request.headers,
        }
        response = Response(data=data)
        response["X-Hook-Secret"] = project.secret
        return response

    def create_webhook_response(self, project: AsanaProject, secret: str) -> Response:
        project.secret = secret
        project.save()
        data = {
            "status": True,
            "message": f"webhook created for project {project.name}",
        }
        response = Response(data=data, status=status.HTTP_201_CREATED)
        response["X-Hook-Secret"] = project.secret
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
