from dataclasses import asdict

from celery import shared_task
from django.conf import settings

from asana.webhook_handlers import WebhookDispatcher

from .client import AsanaApiClient
from .models import AsanaWebhookRequestData
from .repository import AsanaUserRepository
from .use_cases import FetchNewAsanaUsers

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
asana_user_repository = AsanaUserRepository(api_client=asana_api_client)


@shared_task(bind=True, max_retries=1, default_retry_delay=60 * 3)
def process_asana_webhook_task(self, asana_webhook_data_id: int) -> dict | None:
    try:
        webhook_data = AsanaWebhookRequestData.objects.get(pk=asana_webhook_data_id)
        dispatcher = WebhookDispatcher()
        dispatcher_result = dispatcher.dispatch(webhook_data=webhook_data)
        return asdict(dispatcher_result)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task
def fetch_new_asana_users() -> dict:
    use_case = FetchNewAsanaUsers(asana_users_repository=asana_user_repository)
    return use_case.execute()
