from asana.client.exception import AsanaApiClientError
from asana.client.main import AsanaApiClient
from celery import Task as CeleryTask
from celery import shared_task
from django.conf import settings
from message_sender.client.exceptions import AtlasMessageSenderError
from message_sender.client.main import AtlasMessageSender

from .services import NotifyOffboardingCreateTaskService
from .use_cases import NotifyCreatedTasksUseCase

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def mark_asana_task_completed_task(self: CeleryTask) -> None:
    notify_service = NotifyOffboardingCreateTaskService(message_sender=message_sender, asana_client=asana_api_client)
    use_case = NotifyCreatedTasksUseCase(notify_service=notify_service)
    try:
        use_case.execute()
    except (AsanaApiClientError, AtlasMessageSenderError) as error:
        self.retry(exc=error)
