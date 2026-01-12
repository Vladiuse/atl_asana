from celery import shared_task
from common import MessageSender, RequestsSender

from .models import AsanaWebhookRequestData
from .usecase import ProcessAsanaWebhookUseCase

message_sender = MessageSender(request_sender=RequestsSender())


@shared_task
def process_asana_webhook(asana_webhook_id: int) -> None:
    asana_webhook = AsanaWebhookRequestData.objects.select_related("project").get(pk=asana_webhook_id)
    use_case = ProcessAsanaWebhookUseCase()
    use_case.execute(asana_webhook=asana_webhook)
