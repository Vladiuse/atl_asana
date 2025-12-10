from dataclasses import asdict

from celery import shared_task

from asana.webhook_handlers import WebhookDispatcher

from .models import AsanaWebhookRequestData


@shared_task(bind=True, max_retries=1, default_retry_delay=60 * 3)
def process_asana_webhook_task(self, asana_webhook_data_id: int) -> dict | None:
    try:
        webhook_data = AsanaWebhookRequestData.objects.get(pk=asana_webhook_data_id)
        dispatcher = WebhookDispatcher()
        dispatcher_result = dispatcher.dispatch(webhook_data=webhook_data)
        return asdict(dispatcher_result)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
