from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch

import pytest
from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from constance.test import override_config

from creative_quality.models import Task
from creative_quality.services import TaskService

FIELD_NAME = "TEST_FIELD"


@pytest.fixture(autouse=True)
def patch_constance() -> Generator[Any, Any]:
    with override_config(DESIGN_TASK_BAYER_CUSTOM_FIELD_NAME=FIELD_NAME):
        yield


GET_DTO_TEST_DATA = [
    (
        {
            "assignee": {"gid": "12345"},
            "name": "NAME",
            "permalink_url": "URL",
            "custom_fields": [
                {"name": FIELD_NAME, "text_value": "XXX"},
                {"name": "NAME", "text_value": "YYY"},
            ],
        },
        TaskService.TaskData(
            assignee_id="12345",
            name="NAME",
            url="URL",
            bayer_code="XXX",
            work_url="work_url",
        ),
    ),
    (
        {
            "assignee": None,
            "name": "NAME",
            "permalink_url": "URL",
            "custom_fields": [
                {"name": "NAME", "text_value": "YYY"},
            ],
        },
        TaskService.TaskData(
            assignee_id="",
            name="NAME",
            url="URL",
            bayer_code="",
            work_url="work_url",
        ),
    ),
    (
        {
            "assignee": {},
            "name": "NAME",
            "permalink_url": "URL",
            "custom_fields": [
                {"name": "NAME", "text_value": "YYY"},
            ],
        },
        KeyError,
    ),
]


@pytest.fixture(scope="module")
def mock_asana_client() -> Mock:
    return Mock(spec=AsanaApiClient)


@pytest.mark.django_db
class TestTaskService:
    @pytest.mark.parametrize(("data", "expected"), GET_DTO_TEST_DATA)
    def test_get_task_dto(self, data: dict[str, Any], expected: TaskService.TaskData, mock_asana_client: Mock) -> None:
        service = TaskService(asana_api_client=mock_asana_client)
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                service._get_task_dto(task_data=data)
        else:
            assert service._get_task_dto(task_data=data) == expected

    def test_mark_completed_no_error(self, mock_asana_client: Mock) -> None:
        task = Mock(spec=Task)
        service = TaskService(asana_api_client=mock_asana_client)
        service.mark_completed(task=task)
        assert mock_asana_client.mark_task_completed.called
        assert task.is_completed is True
        assert task.save.called

    @pytest.mark.parametrize("error_type", [AsanaNotFoundError, AsanaForbiddenError])
    def test_mark_completed_deleted_task(self, mock_asana_client: Mock, error_type: type[AsanaApiClientError]) -> None:
        task = Mock(spec=Task)
        mock_asana_client.mark_task_completed.side_effect = error_type("error")
        service = TaskService(asana_api_client=mock_asana_client)
        service.mark_completed(task=task)
        assert task.mark_deleted.called

    def test_unexpected_asana_error(self, mock_asana_client: Mock) -> None:
        task = Mock(spec=Task)
        mock_asana_client.mark_task_completed.side_effect = AsanaApiClientError("boom")
        service = TaskService(asana_api_client=mock_asana_client)
        with pytest.raises(AsanaApiClientError):
            service.mark_completed(task=task)

    def test_update_success(self, mock_asana_client: Mock) -> None:
        task = Task.objects.create(task_id="x")
        service = TaskService(asana_api_client=mock_asana_client)
        data = TaskService.TaskData(
            assignee_id="assignee_id",
            bayer_code="bayer_code",
            name="name",
            url="url",
            work_url="work_url",
        )
        with patch.object(service, "_get_task_dto", return_value=data):
            service.update(creative_task=task)
        task.refresh_from_db()
        assert task.assignee_id == "assignee_id"
        assert task.bayer_code == "bayer_code"
        assert task.task_name == "name"
        assert task.url == "url"

    @pytest.mark.parametrize("error_type", [AsanaNotFoundError, AsanaForbiddenError])
    def test_update_error_task_not_exist(self, mock_asana_client: Mock, error_type: type[AsanaApiClientError]) -> None:
        task = Mock(spec=Task)
        mock_asana_client.get_task.side_effect = error_type("error")
        service = TaskService(asana_api_client=mock_asana_client)
        service.update(creative_task=task)
        assert task.mark_deleted.called
        task.mark_error_load_info.assert_not_called()

    def test_update_unexpected_asana_error(self, mock_asana_client: Mock) -> None:
        task = Mock(spec=Task)
        mock_asana_client.get_task.side_effect = AsanaApiClientError("boom")
        service = TaskService(asana_api_client=mock_asana_client)
        service.update(creative_task=task)
        assert task.mark_error_load_info.called
        task.mark_deleted.assert_not_called()
