from asana.client.exception import AsanaApiClientError
from asana.client.main import AsanaApiClient
from asana.models import AsanaWebhookRequestData
from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action
from django.conf import settings
from message_sender.client import AtlasMessageSender
from message_sender.client.exceptions import AtlasMessageSenderError
from retry import retry

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
    @retry(
        exceptions=(AsanaApiClientError, AtlasMessageSenderError),
        tries=3,
        delay=60,
    )
    def _execute_service(
        self,
        service: OffboardingFinanceNotifierService,
        webhook_data: AsanaWebhookRequestData,
    ) -> WebhookActionResult:
        return service.handle_webhook(webhook_data)

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookActionResult:
        service = OffboardingFinanceNotifierService(
            message_sender=message_sender,
            asana_client=asana_api_client,
        )
        return self._execute_service(service=service, webhook_data=webhook_data)
