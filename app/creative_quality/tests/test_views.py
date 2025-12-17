from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from creative_quality.models import Creative, Task


@pytest.fixture()
def creative_task() -> tuple[Creative, Task]:
    task = Task.objects.create(task_id="xxx")
    creative = Creative.objects.create(task=task)
    return creative, task


@pytest.mark.django_db()
class TestCreativeView:
    def test_get(self, creative_task: tuple[Creative, Task], client: Client):
        creative, task = creative_task
        url = reverse(
            "creative_quality:creative_detail",
            kwargs={
                "creative_pk": creative.pk,
                "task_id": task.task_id,
            },
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_not_found(self, client: Client):
        url = reverse(
            "creative_quality:creative_detail",
            kwargs={
                "creative_pk": 1,
                "task_id": 1,
            },
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db()
class TestCreativeEstimateView:
    def test_post(self, creative_task: tuple[Creative, Task], client: Client):
        creative, task = creative_task
        url = reverse(
            "creative_quality:creative_mark_estimate",
            kwargs={
                "creative_pk": creative.pk,
            },
        )
        with patch("creative_quality.views.CreativeService.end_estimate") as mock:
            response = client.post(url)
            assert response.status_code == HTTPStatus.FOUND
            mock.assert_called_once()

    def test_not_found(self, client: Client):
        url = reverse(
            "creative_quality:creative_mark_estimate",
            kwargs={
                "creative_pk": 1,
            },
        )
        response = client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
