# ruff: noqa: S106, S105
from http import HTTPStatus
from unittest.mock import MagicMock, Mock

import pytest
from django.test import Client
from django.urls import reverse

from asana.constants import AsanaResourceType
from asana.models import AsanaWebhook, AsanaWebhookRequestData


@pytest.fixture
def mock_task_delay(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = Mock()
    monkeypatch.setattr("asana.views.process_asana_webhook_task.delay", mock)
    return mock


@pytest.mark.django_db
class TestWebhookView:
    def test_get_method(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        url = reverse("asana:webhook", kwargs={"webhook_name": "x"})
        response = client.get(url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_no_webhook_in_db(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        url = reverse("asana:webhook", kwargs={"webhook_name": "x"})
        response = client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND, f"actual: {response.status_code}"

    def test_no_yet_secret_key(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        webhook_name = "name"
        AsanaWebhook.objects.create(name=webhook_name, resource_id="123", resource_type=AsanaResourceType.PROJECT)
        url = reverse("asana:webhook", kwargs={"webhook_name": webhook_name})
        response = client.post(url)
        assert response.status_code == HTTPStatus.BAD_REQUEST, f"actual: {response.status_code}"
        response_data = response.json()
        assert response_data["success"] is False
        assert webhook_name in response_data["message"]

    def test_send_secret_key(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        webhook = AsanaWebhook.objects.create(name="name", resource_id="123", resource_type=AsanaResourceType.PROJECT)
        headers = {
            "X-Hook-Secret": "string",
        }
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        response = client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        webhook.refresh_from_db()
        assert webhook.secret == "string"

    def test_return_secret_key(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        response = client.post(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers["X-Hook-Secret"] == "xxx"

    def test_save_webhook_data(self, mock_task_delay: MagicMock, client: Client):
        _ = mock_task_delay
        webhook = AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        data = {"y": "y"}
        response = client.post(
            url,
            data=data,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert AsanaWebhookRequestData.objects.count() == 1
        webhook_data = AsanaWebhookRequestData.objects.last()
        assert webhook_data is not None
        assert webhook_data.payload == data, f"actual: {webhook_data.payload}"
        assert webhook_data.webhook == webhook

    def test_run_task(self, mock_task_delay: MagicMock, client: Client):
        AsanaWebhook.objects.create(
            name="name",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
            secret="xxx",
        )
        url = reverse("asana:webhook", kwargs={"webhook_name": "name"})
        data = {"y": "y"}
        response = client.post(
            url,
            data=data,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert AsanaWebhookRequestData.objects.count() == 1
        webhook_data = AsanaWebhookRequestData.objects.last()
        assert webhook_data is not None
        mock_task_delay.assert_called_once_with(asana_webhook_data_id=webhook_data.pk)
