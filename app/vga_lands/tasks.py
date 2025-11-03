from celery import shared_task
from common import MessageSender, RequestsSender

from .models import AsanaWebhookRequestData
from .usecase import ProcessAsanaWebhookUseCase

message_sender = MessageSender(request_sender=RequestsSender())


@shared_task
def process_asana_webhook(asana_webhook_id: int) -> None:
    try:
        asana_webhook = AsanaWebhookRequestData.objects.select_related("project").get(pk=asana_webhook_id)
        usecase = ProcessAsanaWebhookUseCase()
        usecase.execute(asana_webhook=asana_webhook)
    except Exception as error:
        message_sender.send_message(handler="kva_test", message=f"{error.__class__.__name__}: {error}")
        raise error
