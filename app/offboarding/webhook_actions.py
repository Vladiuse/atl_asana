from asana.client.main import AsanaApiClient
from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from django.conf import settings
from message_sender.client import AtlasMessageSender

from .services import OffboardingFinanceNotifierService, OffboardingTaskCreateService

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)


@register_webhook_action(
    name="NotifyTaskCreate",
    description="Offboarding project: Оповещение о новой карточки в проекте в чат HR",
)
class NotifyTaskCreateAction(BaseWebhookAction):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        return OffboardingTaskCreateService().create_from_webhook(webhook_data=webhook_data)


@register_webhook_action(
    name="NotifyOffboardingFinance",
    description="Offboarding project: Оповещает что нужно рассчитать сотрудника",
)
class NotifyOffboardingFinanceAction(BaseWebhookAction):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        service = OffboardingFinanceNotifierService(
            message_sender=message_sender,
            asana_client=asana_api_client,
        )
        return service.handle_webhook(webhook_data)
