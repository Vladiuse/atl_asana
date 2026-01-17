from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock

import pytest
from asana.client import AsanaApiClient
from common import MessageRenderer
from constance import config
from constance.test import override_config
from django.utils import timezone
from message_sender.client import AtlasMessageSender
from message_sender.client.exceptions import AtlasMessageSenderError

from creative_quality.models import Creative, Task, TaskStatus
from creative_quality.services import (
    CreativeService,
    SendEstimationMessageService,
    TaskService,
)

SEND_REMINDER_TRY_COUNT = 3


@pytest.fixture(autouse=True)
def patch_constance() -> Generator[Any, Any, Any]:
    with override_config(SEND_REMINDER_TRY_COUNT=SEND_REMINDER_TRY_COUNT):
        yield


@pytest.fixture
def creative_service() -> CreativeService:
    mock_asana = Mock(spec=AsanaApiClient)
    mock_task_service = Mock(spec=TaskService, asana_api_client=mock_asana)
    creative_service = CreativeService(asana_api_client=mock_asana)
    creative_service.task_service = mock_task_service
    return creative_service


@pytest.fixture
def send_estimate_message_service() -> SendEstimationMessageService:
    return SendEstimationMessageService(
        message_sender=Mock(spec=AtlasMessageSender),
        message_renderer=MessageRenderer(),
    )


@pytest.fixture
def creative() -> Creative:
    task = Task.objects.create(task_id="x", status=TaskStatus.CREATED)
    return Creative.objects.create(task=task)


@pytest.fixture
def fixed_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    fixed = timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0))
    monkeypatch.setattr(timezone, "now", lambda: fixed)
    return fixed


@pytest.mark.django_db
class TestCreativeService:
    @pytest.mark.parametrize("task_status", list(TaskStatus))
    def test_create_creative(self, creative_service: CreativeService, task_status: TaskStatus) -> None:
        task = Task.objects.create(task_id="x", status=task_status)
        creative_service.task_service.update.return_value = task
        creative_service.create_creative(creative_task=task)
        if task_status == TaskStatus.CREATED:
            assert Creative.objects.count() == 1
            assert Creative.objects.filter(task=task).exists()
        else:
            assert Creative.objects.count() == 0
            assert not Creative.objects.filter(task=task).exists()

    def test_estimate_creative(self, creative_service: CreativeService) -> None:
        creative = Mock(spec=Creative)
        creative_service.end_estimate(creative=creative)
        assert creative.mark_rated.called


@pytest.mark.django_db
class TestSendEstimationMessageService:
    VALID_USER_TAG = "adm"

    @pytest.mark.parametrize("bayer_code", ["", "123"])
    @pytest.mark.parametrize("reminder_failure_count_start_value", [0, SEND_REMINDER_TRY_COUNT])
    def test_incorrect_bayer_code(
        self,
        send_estimate_message_service: SendEstimationMessageService,
        fixed_now: datetime,
        reminder_failure_count_start_value: int,
        bayer_code: str,
    ) -> None:
        creative = Mock(spec=Creative)
        creative.task.bayer_code = bayer_code
        creative.reminder_failure_count = reminder_failure_count_start_value
        creative.reminder_fail_reason = ""
        send_estimate_message_service.send_reminder(creative=creative)
        if reminder_failure_count_start_value == 0:
            creative.mark_reminder_limit_reached.assert_not_called()
            assert creative.next_reminder_at == fixed_now + timedelta(hours=config.FAILURE_RETRY_INTERVAL)
        else:
            creative.mark_reminder_limit_reached.assert_called()
        assert creative.reminder_failure_count == reminder_failure_count_start_value + 1
        assert creative.reminder_fail_reason != ""
        creative.save.assert_called()
        send_estimate_message_service.message_sender.send_message_to_user.assert_not_called()

    @pytest.mark.parametrize("reminder_failure_count_start_value", [0, SEND_REMINDER_TRY_COUNT])
    def test_error_send_message(
        self,
        send_estimate_message_service: SendEstimationMessageService,
        fixed_now: datetime,
        reminder_failure_count_start_value: int,
    ) -> None:
        creative = Mock(spec=Creative)
        creative.task.bayer_code = self.VALID_USER_TAG
        creative.reminder_fail_reason = ""
        send_estimate_message_service.message_sender.send_message_to_user.side_effect = AtlasMessageSenderError("boom")
        creative.reminder_failure_count = reminder_failure_count_start_value
        send_estimate_message_service.send_reminder(creative=creative)
        if reminder_failure_count_start_value == 0:
            creative.mark_reminder_limit_reached.assert_not_called()
            assert creative.next_reminder_at == fixed_now + timedelta(hours=config.FAILURE_RETRY_INTERVAL)
        else:
            creative.mark_reminder_limit_reached.assert_called()
        assert creative.reminder_failure_count == reminder_failure_count_start_value + 1
        assert creative.reminder_fail_reason == "boom"
        creative.save.assert_called()
        send_estimate_message_service.message_sender.send_message_to_user.assert_called()

    @pytest.mark.parametrize("reminder_success_count_start_value", [0, SEND_REMINDER_TRY_COUNT])
    def test_send_success(
        self,
        send_estimate_message_service: SendEstimationMessageService,
        fixed_now: datetime,
        reminder_success_count_start_value: int,
    ) -> None:
        creative = Mock(spec=Creative)
        creative.task.bayer_code = self.VALID_USER_TAG
        creative.reminder_fail_reason = ""
        creative.reminder_success_count = reminder_success_count_start_value
        send_estimate_message_service.send_reminder(creative=creative)
        if reminder_success_count_start_value == 0:
            creative.mark_reminder_limit_reached.assert_not_called()
            assert creative.next_reminder_at == fixed_now + timedelta(hours=config.NEXT_SUCCESS_REMINDER_DELTA)
        else:
            creative.mark_reminder_limit_reached.assert_called()
        assert creative.reminder_success_count == reminder_success_count_start_value + 1
        assert creative.reminder_fail_reason == ""
        creative.save.assert_called()
        send_estimate_message_service.message_sender.send_message_to_user.assert_called()

    def test_message(self, send_estimate_message_service: SendEstimationMessageService) -> None:
        task_name = "TASK_NAME"
        url = "https://URL.com"
        send_estimate_message_service._get_estimation_url = Mock(return_value=url)
        creative = Mock(spec=Creative)
        creative.task.bayer_code = self.VALID_USER_TAG
        creative.task.task_name = task_name
        creative.reminder_success_count = 0
        send_estimate_message_service.send_reminder(creative=creative)
        send_estimate_message_service.message_sender.send_message_to_user.assert_called_once()
        _, kwargs = send_estimate_message_service.message_sender.send_message_to_user.call_args
        assert kwargs["user_tags"] == [self.VALID_USER_TAG]
        assert task_name in kwargs["message"]
        assert url in kwargs["message"]
