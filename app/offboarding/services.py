from datetime import timedelta

from asana.constants import AsanaResourceType
from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from constance import config
from django.conf import settings
from django.utils import timezone
from message_sender.client import AtlasMessageSender, Handlers
from message_sender.client.exceptions import AtlasMessageSenderError

from .models import OffboardingTask


class OffboardingTaskCreateService:

    def create_from_webhook(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        target_event_found = False
        for event in webhook_data.payload["events"]:
            if (event["resource"]["resource_type"] == AsanaResourceType.TASK
                and event["parent"]["resource_type"] == AsanaResourceType.PROJECT):
                task_id = event["resource"]["gid"]
                need_notify_at = timezone.now() + timedelta(minutes=config.DELAY_FOR_FEED_CARD)
                OffboardingTask.objects.create(asana_task_id=task_id, notify_at=need_notify_at)
                target_event_found = True

        return WebhookActionResult(
            is_success=target_event_found,
            is_target_event=target_event_found,
        )
    
class NotifyOffboardingTaskService:

    def __init__(self, message_sender: AtlasMessageSender):
        self.message_sender = message_sender
