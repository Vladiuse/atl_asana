import logging
from dataclasses import dataclass
from datetime import timedelta
from email import message
from typing import Any

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from asana.constants import AsanaResourceType
from asana.models import AsanaWebhookRequestData
from asana.utils import get_field_value_from_task
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from common.message_renderer import render_message
from constance import config
from django.utils import timezone
from message_sender.client import AtlasMessageSender, Handlers
from message_sender.client.exceptions import AtlasMessageSenderError
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
