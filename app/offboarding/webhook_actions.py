from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from asana.models import AsanaWebhookRequestData
from asana.constants import AsanaResourceType
from message_sender.client import AtlasMessageSender
from django.conf import settings
from message_sender.client import Handlers
from message_sender.client.exceptions import AtlasMessageSenderError


@register_webhook_action(
    name="NotifyTaskCreate",
    description="Оповещение о новой карточки в проекте в чат HR",
)
class NotifyTaskCreateAction(BaseWebhookAction):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        event_data = webhook_data.payload
        message_sender = AtlasMessageSender(
            host=settings.MESSAGE_SENDER_HOST,
            api_key=settings.DOMAIN_MESSAGE_API_KEY,
        )

        for event in event_data["events"]:
            parent_is_project = event["parent"]["resource_type"] == AsanaResourceType.PROJECT
            resource_is_task = event["resource"]["resource_type"] == AsanaResourceType.TASK
            if resource_is_task and parent_is_project:
                message = ""
                message_sender.send_message(handler=Handlers.KVA_USER)
                return WebhookActionResult(
                    is_success=True,
                    is_target_event=True,
                )

        return WebhookActionResult(
            is_success=False,
            is_target_event=False,
        )
