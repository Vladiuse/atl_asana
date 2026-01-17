from celery import shared_task
from django.conf import settings
from message_sender.client import AtlasMessageSender

from .models import AsanaWebhookRequestData
from .usecase import ProcessAsanaWebhookUseCase

message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)


@shared_task
def process_asana_webhook(asana_webhook_id: int) -> None:
    asana_webhook = AsanaWebhookRequestData.objects.select_related("project").get(pk=asana_webhook_id)
    use_case = ProcessAsanaWebhookUseCase()
    use_case.execute(asana_webhook=asana_webhook)
