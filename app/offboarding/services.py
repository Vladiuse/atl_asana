import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from asana.client import AsanaApiClient
from asana.client.exception import AsanaForbiddenError, AsanaNotFoundError
from asana.constants import AsanaResourceType
from asana.models import AsanaWebhookRequestData
from asana.utils import get_field_value_from_task
from asana.webhook_actions.abstract import WebhookActionResult
from common.message_renderer import render_message
from constance import config
from django.utils import timezone
from message_sender.client import AtlasMessageSender, Handlers
from message_sender.tasks import send_log_message_task

from .exceptions import OffboardingAppError
from .models import OffboardingTask

logger = logging.getLogger(__name__)


class OffboardingTaskCreateService:
    def create_from_webhook(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        target_event_found = False
        for event in webhook_data.payload["events"]:
            if (
                event["resource"]["resource_type"] == AsanaResourceType.TASK
                and event["parent"]["resource_type"] == AsanaResourceType.PROJECT
            ):
                task_id = event["resource"]["gid"]
                need_notify_at = timezone.now() + timedelta(minutes=config.DELAY_FOR_FEED_CARD)
                OffboardingTask.objects.create(asana_task_id=task_id, notify_at=need_notify_at)
                target_event_found = True

        return WebhookActionResult(
            is_success=target_event_found,
            is_target_event=target_event_found,
        )


class NotifyOffboardingTaskService:
    MESSAGE_TEMPLATE = """
    Offboarding

    {{data.fio}}
    {{data.tag}}
    {{data.position}}

    Asana: {{data.url}}
"""

    @dataclass
    class TaskData:
        fio: str
        position: str
        tag: str
        url: str

    def __init__(self, message_sender: AtlasMessageSender, asana_client: AsanaApiClient):
        self.message_sender = message_sender
        self.asana_client = asana_client

    def _get_task_data(self, asana_task_id: str) -> TaskData:
        task_data: dict[str, Any] = self.asana_client.get_task(task_id=asana_task_id)
        fio = get_field_value_from_task(field_name="ФИО", task_data=task_data)
        tag = get_field_value_from_task(field_name="ТЭГ", task_data=task_data)
        position = get_field_value_from_task(field_name="Должность", task_data=task_data)
        url = task_data["permalink_url"]
        if not all([fio, tag, position]):
            raise OffboardingAppError("Not all required fields are filled")
        assert fio is not None  #  noqa: S101
        assert tag is not None  #  noqa: S101
        assert position is not None  #  noqa: S101
        return self.TaskData(fio=fio, position=position, tag=tag, url=url)

    def notify(self, task: OffboardingTask) -> None:
        """Notify about creation new offboarding task.

        Raises:
            AsanaApiClientError: if cant get data from asana
            AtlasMessageSenderError: if can't send message

        """
        try:
            task_data = self._get_task_data(asana_task_id=task.asana_task_id)
            context = {
                "data": task_data,
            }
            message = render_message(
                template=self.MESSAGE_TEMPLATE,
                context=context,
            )
            self.message_sender.send_message(message=message, handler=Handlers.KVA_USER)
            task.status = OffboardingTask.Status.NOTIFIED
            task.save()
        except (AsanaNotFoundError, AsanaForbiddenError) as error:
            task.status = OffboardingTask.Status.DELETED
            task.save()
            logger.warning("Task deleted, task_id: %s, %s", task.asana_task_id, str(error))
        except OffboardingAppError as error:
            logger.exception("Cant process offboarding asana task, id - %s", task.asana_task_id)
            task.status = OffboardingTask.Status.ERROR
            task.save()
            msg = f"⚠️ Cant process offboarding asana task, id - {task.asana_task_id}\n{error}"
            send_log_message_task.delay(message=msg)  # type: ignore[attr-defined]


class OffboardingFinanceNotifier:
    """Handles notifications about employee's financial settlement on offboarding."""

    MESSAGE_TEMPLATE = """
    {{tg_login_name_remind}}
    Offboarding

    {{data.fio}}
    {{data.tag}}
    {{data.position}}

    Сделать расчет по зп
    Asana: {{data.url}}
"""

    def __init__(self, message_sender: AtlasMessageSender, asana_client: AsanaApiClient):
        self.message_sender = message_sender
        self.asana_client = asana_client

    def _get_target_subtasks_names(self) -> set[str]:
        names = config.TARGET_SUB_TASKS_NAMES.split(",")
        return {s.strip() for s in names}

    def _is_completed_task_sub_task(self, webhook_data: AsanaWebhookRequestData) -> None | str:
        """Return task id if completed task in events is subtask."""
        for event in webhook_data.payload["events"]:
            if (
                event["resource"]["resource_type"] == AsanaResourceType.TASK
                and event["parent"]["resource_type"] == AsanaResourceType.SECTION
                and event["parent"]["gid"] == config.OFFBOARDING_COMPLETE_SECTION_ID
            ):
                return event["resource"]["gid"]
        return None

    def _is_task_sub_task(self, task_data: dict[str, Any]) -> bool:
        """Determine whether the task is subtask."""
        parent = task_data["parent"]
        return parent is not None and parent["resource_type"] == AsanaResourceType.TASK

    def is_target_subtask_completed(self, subtasks: list[dict[str, Any]], target_names: set[str]) -> bool:
        """Check list of subtask and return True if complete all subtasks against target."""
        completed_task_names = [task_item["name"] for task_item in subtasks if task_item["completed"] if True]
        return set(completed_task_names) == target_names

    def handle_webhook(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        complete_task_id = self._is_completed_task_sub_task(webhook_data=webhook_data)
        if complete_task_id is None:
            return WebhookActionResult(is_success=True, is_target_event=False)
        assert complete_task_id is not None  # noqa: S101
        task_data = self.asana_client.get_task(task_id=complete_task_id)
        is_sub_task = self._is_task_sub_task(task_data=task_data)
        if is_sub_task is False:
            return WebhookActionResult(is_success=True, is_target_event=False)
        subtasks = self.asana_client.get_sub_tasks(task_id=task_data["gid"], opt_fields=["name", "completed"])
        is_target_subtasks_completed = self.is_target_subtask_completed(
            subtasks=subtasks,
            target_names=self._get_target_subtasks_names(),
        )
        if is_target_subtasks_completed is False:
            return WebhookActionResult(is_success=True, is_target_event=False)
        # context = 
        return WebhookActionResult
