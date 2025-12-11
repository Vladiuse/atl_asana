from asana.client import AsanaApiClient
from celery import shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .use_cases import PingWebhooksUseCase

message_sender = MessageSender(request_sender=RequestsSender())
asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ping_asana_webhook(self) -> dict | None:
    try:
        use_case = PingWebhooksUseCase(
            asana_api_client=asana_client,
            message_sender=MessageSender(request_sender=RequestsSender()),
        )
        return use_case.execute()
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def test_task(self) -> None:
    try:
        raise ZeroDivisionError
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
