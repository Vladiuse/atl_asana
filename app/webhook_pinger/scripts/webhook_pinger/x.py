import logging

from asana.client import AsanaApiClient
from common import MessageSender, RequestsSender
from django.conf import settings
from webhook_pinger.use_cases import PingWebhooksUseCase

asana_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)
logging.basicConfig(level=logging.INFO)


use_case = PingWebhooksUseCase(
    asana_api_client=asana_client,
    message_sender=MessageSender(request_sender=RequestsSender()),
)


def run() -> None:
    result = use_case.execute()
    print(result)
