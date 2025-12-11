from asana.client import AsanaApiClient
from celery import shared_task
from celery.app.task import Task as CeleryTask
from common import MessageSender, RequestsSender
from django.conf import settings

from .models import Task
from .services import UpdateTaskInfoService

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


@shared_task(bind=True, max_retries=1, default_retry_delay=1 * 3600)
def mark_asana_task_completed_task(self: CeleryTask, task_pk: int) -> None:
    task_service = UpdateTaskInfoService(asana_api_client=asana_api_client)
    try:
        task = Task.objects.get(pk=task_pk)
        task_service.mark_completed(task=task)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
