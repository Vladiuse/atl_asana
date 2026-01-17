import logging

from asana.client import AsanaApiClient
from asana.constants import ATLAS_WORKSPACE_ID
from message_sender.client import AtlasMessageSender

from .models import Webhook


class PingWebhooksUseCase:
    def __init__(self, asana_api_client: AsanaApiClient, message_sender: AtlasMessageSender):
        self.asana_api_client = asana_api_client
        self.message_sender = message_sender

    def execute(self) -> dict[str, int]:
        webhooks_db_count = Webhook.objects.count()
        asana_webhooks_data = self.asana_api_client.get_webhooks(workspace_id=ATLAS_WORKSPACE_ID)
        atlas_webhook_ids = [asana_webhook["gid"] for asana_webhook in asana_webhooks_data]
        logging.info("atlas_webhook_ids: %s", atlas_webhook_ids)
        if webhooks_db_count != len(atlas_webhook_ids):
            message = f"Число вебхуков не совпадает, на сервере {len(atlas_webhook_ids)}, в БД {webhooks_db_count}"
            self.message_sender.send_log_message(message=message)
        return {
            "webhooks_db_count": webhooks_db_count,
            "atlas_webhooks_count": len(atlas_webhook_ids),
        }
