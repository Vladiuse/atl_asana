import logging

from asana.client import AsanaApiClient
from asana.repository import AsanaUserRepository
from comment_notifier.use_cases import FetchMissingProjectCommentsUseCase
from common import MessageSender, RequestsSender
from django.conf import settings

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)

message_sender = MessageSender(request_sender=RequestsSender())
repository = AsanaUserRepository(api_client=asana_client)


def run() -> None:
    use_case = FetchMissingProjectCommentsUseCase(
        asana_api_client=asana_client,
    )
    use_case.execute()
