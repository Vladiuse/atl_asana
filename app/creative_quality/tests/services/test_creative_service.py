from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError
from common import MessageRenderer, MessageSender
from constance import config
from constance.test import override_config
from django.utils import timezone

from creative_quality.models import Creative, Task, TaskStatus
from creative_quality.services import (
    CreativeEstimationData,
    CreativeService,
    SendEstimationMessageService,
    TaskService,
)

SEND_REMINDER_TRY_COUNT = 3


@pytest.fixture(autouse=True)
def patch_constance():
    with override_config(SEND_REMINDER_TRY_COUNT=SEND_REMINDER_TRY_COUNT):
        yield


@pytest.fixture()
def creative_service() -> CreativeService:
    mock_asana = Mock(spec=AsanaApiClient)
    mock_task_service = Mock(spec=TaskService, asana_api_client=mock_asana)
    creative_service = CreativeService(asan_api_client=mock_asana)
    creative_service.task_service = mock_task_service
    return creative_service


@pytest.fixture()
def estimate_data() -> CreativeEstimationData:
    return CreativeEstimationData(
        hold=1,
        hook=2,
        ctr=3,
        comment="123",
        need_complete_task=True,
    )


@pytest.fixture()
def estimate_data_not_need_check() -> CreativeEstimationData:
    return CreativeEstimationData(
        hold=1,
        hook=2,
        ctr=3,
        comment="123",
        need_complete_task=False,
    )


@pytest.fixture()
def send_estimate_message_service() -> SendEstimationMessageService:
    return SendEstimationMessageService(
        message_sender=Mock(spec=MessageSender),
        message_renderer=MessageRenderer(),
    )


@pytest.fixture()
def creative() -> Creative:
    task = Task.objects.create(task_id="x", status=TaskStatus.CREATED)
    return Creative.objects.create(task=task)


@pytest.fixture()
def fixed_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    fixed = timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0))
    monkeypatch.setattr(timezone, "now", lambda: fixed)
    return fixed


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

    def test_estimate_creative(self, creative_service: CreativeService, estimate_data: CreativeEstimationData):
        creative = Mock(spec=Creative)
        creative_service.estimate(creative=creative, estimate_data=estimate_data)
        assert creative.mark_rated.called
        assert creative_service.task_service.mark_completed.called
        assert creative.hold == 1
        assert creative.hook == 2  # noqa: PLR2004
        assert creative.ctr == 3  # noqa: PLR2004
        assert creative.comment == "123"

    def test_estimate_creative_need_complete(
        self,
        creative_service: CreativeService,
        estimate_data: CreativeEstimationData,
    ):
        creative = Mock(spec=Creative)
        creative_service.task_service.mark_completed.side_effect = AsanaApiClientError("boom")
        with patch("creative_quality.tasks.mark_asana_task_completed_task.apply_async") as mock_task:
            creative_service.estimate(creative=creative, estimate_data=estimate_data)
            assert mock_task.called

    def test_estimate_creative_not_need_complete(
        self,
        creative_service: CreativeService,
        estimate_data_not_need_check: CreativeEstimationData,
    ):
        creative = Mock(spec=Creative)
        creative_service.task_service.mark_completed.assert_not_called()
        with patch("creative_quality.tasks.mark_asana_task_completed_task.apply_async") as mock_task:
            creative_service.estimate(creative=creative, estimate_data=estimate_data_not_need_check)
            mock_task.assert_not_called()


@pytest.mark.django_db()
class TestSendEstimationMessageService:
    @pytest.mark.parametrize("reminder_failure_count_start_value", [0, SEND_REMINDER_TRY_COUNT])
    def test_empty_bayer_code_no_limit(
        self,
        send_estimate_message_service: SendEstimationMessageService,
        fixed_now: datetime,
        reminder_failure_count_start_value: int,
    ):
        creative = Mock(spec=Creative)
        creative.task.bayer_code = ""
        creative.reminder_failure_count = reminder_failure_count_start_value
        send_estimate_message_service.send_reminder(creative=creative)
        if reminder_failure_count_start_value == 0:
            creative.mark_reminder_limit_reached.assert_not_called()
            assert creative.next_reminder_at == fixed_now + timedelta(hours=config.FAILURE_RETRY_INTERVAL)
        else:
            creative.mark_reminder_limit_reached.assert_called()
        assert creative.reminder_failure_count == reminder_failure_count_start_value + 1
        assert creative.reminder_fail_reason != ""
        creative.save.assert_called()
