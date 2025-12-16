from asana.client import AsanaApiClient
from celery import shared_task
from celery.app.task import Task as CeleryTask
from common import MessageRenderer, MessageSender, RequestsSender
from django.conf import settings

from .models import Task
from .services import CreativeProjectSectionService, CreativeService, SendEstimationMessageService, TaskService
from .use_cases import (
    CreateCreativesForNewTasksUseCase,
    CreativesOverDueForEstimateUseCase,
    DataIntegrityCheckUseCase,
    FetchMissingTasksUseCase,
    SendCreativesToGoogleSheetUseCase,
    SendEstimationMessageUseCase,
)

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())
message_renderer = MessageRenderer()


@shared_task(bind=True, max_retries=1, default_retry_delay=1 * 3600)
def mark_asana_task_completed_task(self: CeleryTask, task_pk: int) -> None:
    task_service = TaskService(asana_api_client=asana_api_client)
    try:
        task = Task.objects.get(pk=task_pk)
        task_service.mark_completed(task=task)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task
def create_creatives_for_new_task() -> dict:
    creative_service = CreativeService(asan_api_client=asana_api_client)
    use_case = CreateCreativesForNewTasksUseCase(creative_service=creative_service)
    return use_case.execute()


@shared_task
def update_overdue_creatives_task() -> dict:
    return CreativesOverDueForEstimateUseCase().execute()


@shared_task
def send_estimation_message_task() -> dict:
    estimation_service = SendEstimationMessageService(message_sender=message_sender, message_renderer=message_renderer)
    use_case = SendEstimationMessageUseCase(estimation_service=estimation_service)
    return use_case.execute()


@shared_task
def fetch_missing_section_tasks_task() -> dict:
    creative_project_section_service = CreativeProjectSectionService(asana_api_client=asana_api_client)
    use_case = FetchMissingTasksUseCase(creative_project_section_service=creative_project_section_service)
    return use_case.execute()


@shared_task
def add_new_creatives_in_gs_table() -> dict:
    return SendCreativesToGoogleSheetUseCase().execute()


@shared_task
def add_test_creative_to_table_task() -> dict:
    return SendCreativesToGoogleSheetUseCase().send_test_creative_to_table()


@shared_task
def data_integrity_check_task() -> None:
    DataIntegrityCheckUseCase().execute()
