from dataclasses import asdict

from asana.client import AsanaApiClient
from celery import Task, shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .models import AsanaComment, AsanaWebhookRequestData
from .services import LoadCommentsAdditionalInfo, ProcessAsanaNewCommentEvent
from .use_cases import (
    AsanaCommentNotifierUseCase,
    FetchMissingProjectCommentsUseCase,
)

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


@shared_task(bind=True, max_retries=2, default_retry_delay=60 * 5)
def notify_new_asana_comments_tasks(self: Task, comment_id: str) -> None:  # type: ignore[type-arg]
    try:
        use_case = AsanaCommentNotifierUseCase(asana_api_client=asana_api_client, message_sender=message_sender)
        return use_case.execute(comment_id=comment_id)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def process_asana_new_comments_task(self: Task, asana_webhook_id: int) -> dict | None:  # type: ignore[type-arg]
    try:
        asana_webhook = AsanaWebhookRequestData.objects.get(pk=asana_webhook_id)
        result = ProcessAsanaNewCommentEvent().process(asana_webhook)
        for asana_new_comment_event in result.comments:
            notify_new_asana_comments_tasks.apply_async(  # type: ignore[attr-defined]
                args=[asana_new_comment_event.comment_id],
                countdown=60,
            )
        return asdict(result)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
        return None


@shared_task(bind=True, max_retries=1, default_retry_delay=60 * 3)
def fetch_missing_project_comments_task(self: Task, *, send_messages: bool = True) -> dict | None:  # type: ignore[type-arg]
    try:
        use_case = FetchMissingProjectCommentsUseCase(asana_api_client=asana_api_client)
        return use_case.execute(send_messages=send_messages)
    except Exception as error:  # noqa: BLE001
        self.retry(exc=error)
        return None


@shared_task()
def fetch_comment_tasks_urls_task() -> dict[str, int]:
    queryset = AsanaComment.objects.all()
    use_case = LoadCommentsAdditionalInfo(asana_api_client=asana_api_client)
    return use_case.load(queryset=queryset)
