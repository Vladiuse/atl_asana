from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client
from django.urls import reverse

from creative_quality.models import Creative, Task
from creative_quality.services import CreativeEstimationData


@pytest.fixture()
def task() -> Task:
    return Task.objects.create(task_id="xxx")


@pytest.mark.django_db()
class TestEstimateCreativeView:
    @patch("creative_quality.views.CreativeService.estimate")
    def test_post_valid_data(self, mock_estimate_method: MagicMock, client: Client, task: Task):
        creative = Creative.objects.create(task=task)
        url = reverse(
            "creative_quality:update-creative",
            kwargs={
                "task_id": task.task_id,
                "creative_id": creative.pk,
            },
        )
        data = {
            "hook": 1,
            "hold": 2,
            "ctr": 3,
            "comment": "123",
        }
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        estimate_data = CreativeEstimationData(
            hook=1,
            hold=2,
            ctr=3,
            comment="123",
            need_complete_task=True,
        )
        mock_estimate_method.assert_called_once_with(creative=creative, estimate_data=estimate_data)

    @patch("creative_quality.views.CreativeService.estimate")
    def test_post_invalid_data(self, mock_estimate_method: MagicMock, client: Client, task: Task):
        creative = Creative.objects.create(task=task)
        url = reverse(
            "creative_quality:update-creative",
            kwargs={
                "task_id": task.task_id,
                "creative_id": creative.pk,
            },
        )
        data = {
            "hook": "a",
            "hold": "b",
            "ctr": 3,
            "comment": "123",
        }
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.OK
        mock_estimate_method.assert_not_called()
