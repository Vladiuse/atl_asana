from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action

from .services import OffboardingTaskCreateService


@register_webhook_action(
    name="NotifyTaskCreate",
    description="Оповещение о новой карточки в проекте в чат HR",
)
class NotifyTaskCreateAction(BaseWebhookAction):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        return OffboardingTaskCreateService().create_from_webhook(webhook_data=webhook_data)
