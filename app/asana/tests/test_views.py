from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from asana.models import AsanaResourceType, AsanaWebhook, AsanaWebhookRequestData


@patch("asana.views.process_asana_webhook_task.delay", return_value=None)
class WebhookViewTest(TestCase):
    def setUp(self):
        self.factory = Client()

    def test_get_method(self, mock_task: MagicMock):
        _ = mock_task
        url = reverse("asana:webhook", kwargs={"webhook_name": "x"})
        response = self.factory.get(url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_no_webhook_in_db(self, mock_task: MagicMock):
        _ = mock_task
        url = reverse("asana:webhook", kwargs={"webhook_name": "x"})
        response = self.factory.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND, f"actual: {response.status_code}"

    def test_no_yet_secret_key(self, mock_task: MagicMock):
        _ = mock_task
        webhook_name = "xxxyyyxxx"
        AsanaWebhook.objects.create(name=webhook_name, resource_id="123", resource_type=AsanaResourceType.PROJECT)
        url = reverse("asana:webhook", kwargs={"webhook_name": webhook_name})
        response = self.factory.post(url)
        assert response.status_code == HTTPStatus.BAD_REQUEST, f"actual: {response.status_code}"
        response_data = response.json()
        assert response_data["success"] is False
        assert webhook_name in response_data["message"]

    def test_send_secret_key(self, mock_task: MagicMock):
        _ = mock_task
        webhook = AsanaWebhook.objects.create(name="name", resource_id="123", resource_type=AsanaResourceType.PROJECT)
        headers = {
            "X-Hook-Secret": "xxx",
        }
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        response = self.factory.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        webhook.refresh_from_db()
        assert webhook.secret == "xxx"

    def test_return_secret_key(self, mock_task: MagicMock):
        _ = mock_task
        AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        response = self.factory.post(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers["X-Hook-Secret"] == "xxx"

    def test_save_webhook_data(self, mock_task: MagicMock):
        _ = mock_task
        webhook = AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        data = {"y": "y"}
        response = self.factory.post(
            url,
            data=data,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert AsanaWebhookRequestData.objects.count() == 1
        webhook_data = AsanaWebhookRequestData.objects.last()
        assert webhook_data.payload == data, f"actual: {webhook_data.payload}"
        assert webhook_data.webhook == webhook

    def test_run_task(self, mock_task: MagicMock):
        AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        data = {"y": "y"}
        response = self.factory.post(
            url,
            data=data,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert AsanaWebhookRequestData.objects.count() == 1
        webhook_data = AsanaWebhookRequestData.objects.last()
        mock_task.assert_called_once_with(asana_webhook_data_id=webhook_data.pk)
