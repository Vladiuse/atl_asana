from unittest.mock import Mock

import pytest
from asana.client import AsanaApiClient

from creative_quality.models import Creative, Task, TaskStatus
from creative_quality.services import CreativeService, TaskService


@pytest.fixture()
def creative_service() -> CreativeService:
    mock_asana = Mock(spec=AsanaApiClient)
    mock_task_service = Mock(spec=TaskService, asana_api_client=mock_asana)
    creative_service = CreativeService(asan_api_client=mock_asana)
    creative_service.task_service = mock_task_service
    return creative_service


@pytest.mark.django_db()
class TestCreativeService:
    @pytest.mark.parametrize("task_status", list(TaskStatus))
    def test_create_creative(self, creative_service: CreativeService, task_status: TaskStatus):
        task = Task.objects.create(task_id="x", status=task_status)
        creative_service.task_service.update.return_value = task
        creative_service.create_creative(creative_task=task)
        if task_status == TaskStatus.CREATED:
            assert Creative.objects.count() == 1
            assert Creative.objects.filter(task=task).exists()
        else:
            assert Creative.objects.count() == 0
            assert not Creative.objects.filter(task=task).exists()

