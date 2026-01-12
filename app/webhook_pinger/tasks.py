# mypy: disable-error-code=type-arg
from asana.client import AsanaApiClient
from celery import Task, shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .use_cases import PingWebhooksUseCase

message_sender = MessageSender(request_sender=RequestsSender())
asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ping_asana_webhook(self: Task) -> dict | None:
    use_case = PingWebhooksUseCase(
        asana_api_client=asana_client,
        message_sender=MessageSender(request_sender=RequestsSender()),
    )
    try:
        return use_case.execute()
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
        return None


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def test_task(self: Task) -> None:
    try:
        raise ZeroDivisionError  # noqa: TRY301
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
