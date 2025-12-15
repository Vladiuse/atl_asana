from asana.client import AsanaApiClient
from celery import shared_task
from celery.app.task import Task as CeleryTask
from common import MessageSender, RequestsSender
from django.conf import settings
from django.utils import timezone

from .models import Creative, CreativeStatus, Task
from .services import CreativeProjectSectionService, TaskService
from .use_cases import FetchMissingTasksUseCase

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


@shared_task(bind=True, max_retries=1, default_retry_delay=1 * 3600)
def mark_asana_task_completed_task(self: CeleryTask, task_pk: int) -> None:
    task_service = TaskService(asana_api_client=asana_api_client)
    try:
        task = Task.objects.get(pk=task_pk)
        task_service.mark_completed(task=task)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task
def update_overdue_creatives() -> None:
    """
    # Mark creatives as NEED_REVIEW if their need_rated_at date is older than 3(or other value) days
    """
    creatives = Creative.objects.filter(
        status=CreativeStatus.WAITING,
        need_rated_at__lte=timezone.now(),
    )
    for creative in creatives:
        creative.mark_need_estimate()


@shared_task
def fetch_missing_section_tasks_task() -> dict:
    creative_project_section_service = CreativeProjectSectionService(asana_api_client=asana_api_client)
    use_case = FetchMissingTasksUseCase(creative_project_section_service=creative_project_section_service)
    return use_case.execute()
