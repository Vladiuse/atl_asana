from asana.client import AsanaApiClient
from celery import shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .use_cases import PingWebhooksUseCase

message_sender = MessageSender(request_sender=RequestsSender())
asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


@shared_task
def ping_asana_webhook() -> None:
    use_case = PingWebhooksUseCase(
        asana_api_client=asana_client,
        message_sender=MessageSender(request_sender=RequestsSender()),
    )
    try:
        use_case.execute()
    except Exception as error:
        message_sender.send_message(
            handler="kva_test",
            message=f"ping_asana_webhook {error.__class__.__name__}: {error}",
        )
        raise error
