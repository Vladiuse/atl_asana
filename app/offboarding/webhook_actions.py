from asana.client.exception import AsanaApiClientError
from asana.client.main import AsanaApiClient
from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from django.conf import settings
from message_sender.client import AtlasMessageSender
from message_sender.client.exceptions import AtlasMessageSenderError
from retry import retry

from .services import OffboardingTaskCompleteService, OffboardingTaskCreateService

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
    @retry(
        exceptions=(AsanaApiClientError, AtlasMessageSenderError),
        tries=3,
        delay=60,
    )
    def _execute_service(
        self,
        service: OffboardingTaskCreateService,
        webhook_data: AsanaWebhookRequestData,
    ) -> WebhookActionResult:
        return service.create_from_webhook(webhook_data)

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        service = OffboardingTaskCreateService()
        return self._execute_service(service=service, webhook_data=webhook_data)


@register_webhook_action(
    name="OffboardingTaskCompleteAction",
    description="Offboarding project: Помечает таск завершенным",
)
class OffboardingTaskCompleteAction(BaseWebhookAction):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        service = OffboardingTaskCompleteService()
        return service.detect_is_complete(webhook_data=webhook_data)
