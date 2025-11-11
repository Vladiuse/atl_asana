from dataclasses import asdict

from asana.client import AsanaApiClient
from celery import shared_task
from common import MessageSender, RequestsSender
from django.conf import settings

from .models import AsanaWebhookRequestData
from .services import ProcessAsanaNewCommentEvent
from .use_cases import FetchCommentTaskUrls

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
message_sender = MessageSender(request_sender=RequestsSender())


@shared_task
def process_asana_new_comments_task(asana_webhook_id: int) -> dict:
    try:
        asana_webhook = AsanaWebhookRequestData.objects.get(pk=asana_webhook_id)
        result = ProcessAsanaNewCommentEvent().process(asana_webhook)
        return asdict(result)
    except Exception as error:
        message_sender.send_message(
            handler="kva_test",
            message=f"process_asana_new_comments {error.__class__.__name__}: {error}",
        )
        raise error


@shared_task
def fetch_comment_tasks_urls_task() -> dict:
    try:
        use_case = FetchCommentTaskUrls(asana_api_client=asana_api_client)
        return use_case.execute()
    except Exception as error:
        message_sender.send_message(
            handler="kva_test",
            message=f"fetch_comment_tasks_urls_task {error.__class__.__name__}: {error}",
        )
        raise error
