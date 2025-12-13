from unittest.mock import Mock

import pytest
from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from constance.test import override_config

from creative_quality.models import Task
from creative_quality.services import TaskService

GET_DTO_TEST_DATA = [
    (
        {
            "assignee": {"gid": "12345"},
            "name": "NAME",
            "permalink_url": "URL",
            "custom_fields": [
                {"name": "TEST_FIELD", "text_value": "XXX"},
                {"name": "NAME", "text_value": "YYY"},
            ],
        },
        TaskService.TaskData(
            assignee_id="12345",
            name="NAME",
            url="URL",
            bayer_code="XXX",
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


@pytest.fixture(autouse=True)
def patch_constance():
    with override_config(DESIGN_TASK_BAER_CUSTOM_FIELD_NAME="TEST_FIELD"):
        yield


@pytest.fixture(scope="module")
def mock_asana_client() -> Mock:
    return Mock(spec=AsanaApiClient)


@pytest.mark.django_db()
class TestTaskService:
    @pytest.mark.parametrize(("data", "expected"), GET_DTO_TEST_DATA)
    def test_get_task_dto(self, data: dict, expected: TaskService.TaskData, mock_asana_client: Mock):
        service = TaskService(asana_api_client=mock_asana_client)
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                service._get_task_dto(task_data=data)
        else:
            assert service._get_task_dto(task_data=data) == expected

    def test_mark_completed_no_error(self, mock_asana_client: Mock):
        task = Mock(spec=Task)
        service = TaskService(asana_api_client=mock_asana_client)
        service.mark_completed(task=task)
        assert mock_asana_client.mark_task_completed.called
        assert task.is_completed is True
        assert task.save.called

    @pytest.mark.parametrize("error_type", [AsanaNotFoundError, AsanaForbiddenError])
    def test_mark_completed_deleted_task(self, mock_asana_client: Mock, error_type: type[AsanaApiClientError]):
        task = Mock(spec=Task)
        mock_asana_client.mark_task_completed.side_effect = error_type("error")
        service = TaskService(asana_api_client=mock_asana_client)
        service.mark_completed(task=task)
        assert task.mark_deleted.called

    def test_unexpected_asana_error(self, mock_asana_client: Mock):
        task = Mock(spec=Task)
        mock_asana_client.mark_task_completed.side_effect = AsanaApiClientError("boom")
        service = TaskService(asana_api_client=mock_asana_client)
        with pytest.raises(AsanaApiClientError):
            service.mark_completed(task=task)
