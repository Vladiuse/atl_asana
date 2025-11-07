from dataclasses import asdict

from celery import shared_task
from common import MessageSender, RequestsSender

from .models import AsanaWebhookRequestData
from .services import ProcessAsanaNewCommentEvent

message_sender = MessageSender(request_sender=RequestsSender())


@shared_task
def process_asana_new_comments_task(asana_webhook_id: int) -> dict:
    try:
        asana_webhook = AsanaWebhookRequestData.objects.get(pk=asana_webhook_id)
        result = ProcessAsanaNewCommentEvent().process(events_data=asana_webhook.payload)
        return asdict(result)
    except Exception as error:
        message_sender.send_message(
            handler="kva_test", message=f"process_asana_new_comments {error.__class__.__name__}: {error}",
        )
        raise error
