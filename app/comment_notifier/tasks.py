from dataclasses import asdict

from asana.client import AsanaApiClient
from celery import shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .models import AsanaComment, AsanaWebhookRequestData
from .services import ProcessAsanaNewCommentEvent
from .use_cases import (
    AsanaCommentNotifierUseCase,
    FetchCommentsAdditionalInfoUseCase,
    FetchMissingProjectCommentsUseCase,
)

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def process_asana_new_comments_task(self, asana_webhook_id: int) -> dict | None:
    try:
        asana_webhook = AsanaWebhookRequestData.objects.get(pk=asana_webhook_id)
        result = ProcessAsanaNewCommentEvent().process(asana_webhook)
        return asdict(result)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def fetch_missing_project_comments_task(self) -> dict | None:
    try:
        use_case = FetchMissingProjectCommentsUseCase(asana_api_client=asana_api_client)
        return use_case.execute()
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task()
def notify_new_asana_comments_tasks() -> dict:
    use_case = AsanaCommentNotifierUseCase(asana_api_client=asana_api_client, message_sender=message_sender)
    return use_case.execute()


@shared_task()
def fetch_comment_tasks_urls_task() -> dict:
    queryset = AsanaComment.objects.all()
    use_case = FetchCommentsAdditionalInfoUseCase(asana_api_client=asana_api_client)
    return use_case.execute(queryset=queryset)
