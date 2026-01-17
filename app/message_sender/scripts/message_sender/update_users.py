from django.conf import settings

from message_sender.client import AtlasMessageSender
from message_sender.services import UserService

client = AtlasMessageSender(
    host=settings.MESSAGE_SENDER_HOST,
    api_key=settings.DOMAIN_MESSAGE_API_KEY,
)

service = UserService(message_sender_client=client)
def run() -> None:
    result = service.update_all_users()
    print(result)
