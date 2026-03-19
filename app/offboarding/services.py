import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from asana.constants import AsanaResourceType, AtlasProject
from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import WebhookActionResult
from common.message_renderer import render_message
from constance import config
from django.utils import timezone
from message_sender.client import AtlasMessageSender, Handlers

from .exceptions import OffboardingAppError
from .extractors import extract_offboarding_task_data
from .models import OffboardingTask

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .dto import TaskData


class OffboardingTaskCreateService:
    def create_task(self, task_id: str) -> OffboardingTask:
        need_notify_at = timezone.now() + timedelta(minutes=config.DELAY_FOR_FEED_CARD)
        return OffboardingTask.objects.create(asana_task_id=task_id, notified_created_at=need_notify_at)

    def create_from_webhook(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        target_event_found = False
        for event in webhook_data.payload["events"]:
            if (
                event["resource"]["resource_type"] == AsanaResourceType.TASK
                and event["parent"]["resource_type"] == AsanaResourceType.PROJECT
                and event["parent"]["gid"] == AtlasProject.OFFBOARDING.value
            ):
                task_id = event["resource"]["gid"]
                self.create_task(task_id=task_id)
                target_event_found = True

        return WebhookActionResult(
            is_success=True,
            is_target_event=target_event_found,
        )


class OffboardingTaskCompleteService:
    def detect_is_complete(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        target_event_found = False
        for event in webhook_data.payload["events"]:
            if (
                event["resource"]["resource_type"] == AsanaResourceType.TASK
                and event["parent"]["resource_type"] == AsanaResourceType.SECTION
                and event["parent"]["gid"] == config.OFFBOARDING_COMPLETE_SECTION_ID
            ):
                task_id = event["resource"]["gid"]
                OffboardingTask.objects.filter(asana_task_id=task_id).update(status=OffboardingTask.Status.COMPLETED)
                target_event_found = True
                logger.debug("Complete task %s, webhook_data: %s", task_id, webhook_data)
        return WebhookActionResult(
            is_success=True,
            is_target_event=target_event_found,
        )


class NotifyOffboardingCreateTaskService:
    MESSAGE_TEMPLATE = """
    Offboarding:<br>

    {{data.fio}}
    {{data.tag}}
    {{data.position}}<br>

    Asana: {{data.url}}
"""

    def __init__(self, message_sender: AtlasMessageSender, asana_client: AsanaApiClient):
        self.message_sender = message_sender
        self.asana_client = asana_client

    def notify(self, task: OffboardingTask) -> None:
        """Notify about creation new offboarding task.

        Raises:
            AsanaApiClientError: if cant get data from asana
            AtlasMessageSenderError: if can't send message
            OffboardingAppError: if task fields not filled
        """
        try:
            task_data: dict[str, Any] = self.asana_client.get_task(task_id=task.asana_task_id)
            task_dto: TaskData = extract_offboarding_task_data(task_data)
            logger.debug("Task id: %s, %s", task.asana_task_id, task_dto)
            context = {
                "data": task_dto,
            }
            message = render_message(
                template=self.MESSAGE_TEMPLATE,
                context=context,
            )
            self.message_sender.send_message(message=message, handler=Handlers.KVA_USER)
            task.notified_created = True
            task.save()
        except (AsanaNotFoundError, AsanaForbiddenError) as error:
            task.status = OffboardingTask.Status.DELETED
            task.save()
            logger.warning("Task deleted, task_id: %s, %s", task.asana_task_id, str(error))
        except OffboardingAppError as error:
            logger.exception("Cant process offboarding asana task, id - %s", task.asana_task_id)
            task.status = OffboardingTask.Status.ERROR
            task.save()
            raise error


class OffboardingFinanceNotifierService:
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

    def _is_target_subtask_completed(self, subtasks: list[dict[str, Any]], target_names: set[str]) -> bool:
        """Check list of subtask and return True if all target subtasks are completed."""
        completed_task_names = {task_item["name"] for task_item in subtasks if task_item["completed"] is False}
        logger.debug("Target subtasks names: %s", target_names)
        logger.debug("Not completed subtasks: %s", completed_task_names)
        return completed_task_names == target_names

    def notify(self, task: OffboardingTask) -> None:
        """Notify if left few target subtasks.

        All of subtasks must be completed, against few target subtasks.

        Raises:
            AsanaApiClientError: if cant get data from asana
            AtlasMessageSenderError: if can't send message
            OffboardingAppError: if task dont have full data.

        """
        logger.debug("Check subtasks of %s", task.asana_task_id)
        try:
            subtasks = self.asana_client.get_sub_tasks(task_id=task.asana_task_id, opt_fields=["name", "completed"])
        except (AsanaForbiddenError, AsanaNotFoundError) as error:
            task.status = OffboardingTask.Status.DELETED
            task.save()
            logger.warning("Task deleted, task_id: %s, %s", task.asana_task_id, str(error))
            return
        logger.debug("Task %s Subtasks: %s", task.asana_task_id, subtasks)
        is_target_subtasks_completed = self._is_target_subtask_completed(
            subtasks=subtasks,
            target_names=self._get_target_subtasks_names(),
        )
        if is_target_subtasks_completed is False:
            return
        task_data = self.asana_client.get_task(task_id=task.asana_task_id)
        try:
            task_dto: TaskData = extract_offboarding_task_data(task_data)
        except 
        logger.debug("TaskData: %s", task_dto)
        context = {
            "data": task_dto,
            "tg_login_name_remind": config.PAYROLL_RESPONSIBLE_TELEGRAM_LOGIN,
        }
        message = render_message(
            template=self.MESSAGE_TEMPLATE,
            context=context,
        )
        self.message_sender.send_message(message=message, handler=Handlers.KVA_USER)
        logger.debug("Task %s Notified", task.asana_task_id)
        task.notified_need_payroll = True
        task.save()
