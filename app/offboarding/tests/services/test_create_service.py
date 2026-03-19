from typing import Any
from unittest.mock import Mock

import pytest
from asana.models import AsanaWebhookRequestData

from offboarding.models import OffboardingTask
from offboarding.services import OffboardingTaskCreateService
from offboarding.tests.fixtures_data import (
    CREATE_SUB_TASK_EVENT,
    CREATE_TASK_EVENT,
    CREATE_TASK_EVENT_CORRECT_PROJECT,
    RESOURCE_ID,
)

NOT_TARGET_RESOURCE = {
    "events": [
        {
            "user": {"gid": "1213537811762722", "resource_type": "user"},
            "action": "XXX",
            "parent": {"gid": "123123123", "resource_type": "task", "resource_subtype": "default_task"},
            "resource": {"gid": "1213717492740875", "resource_type": "XXX", "resource_subtype": "default_task"},
            "created_at": "2026-03-17T10:11:18.514Z",
        },
    ],
}


@pytest.mark.django_db
class TestCreateService:
    @pytest.mark.parametrize(
        ("event_data", "is_must_create"),
        [
            (CREATE_TASK_EVENT_CORRECT_PROJECT, True),
            (CREATE_TASK_EVENT, False),
            (CREATE_SUB_TASK_EVENT, False),
            (NOT_TARGET_RESOURCE, False),
        ],
    )
    def test_create_from_webhook_data(self, event_data: dict[str, Any], is_must_create: bool) -> None:
        service = OffboardingTaskCreateService()
        mock_webhook = Mock(spec=AsanaWebhookRequestData)
        mock_webhook.payload = event_data
        result = service.create_from_webhook(webhook_data=mock_webhook)
        assert OffboardingTask.objects.exists() == is_must_create
        assert result.is_success is True
        if is_must_create:
            assert OffboardingTask.objects.filter(asana_task_id=RESOURCE_ID).exists() is True
            assert result.is_target_event is True
        else:
            assert result.is_target_event is False
