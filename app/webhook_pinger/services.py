from asana.client import AsanaApiClient
from asana.constants import ATLAS_WORKSPACE_ID

from .models import Webhook


class AddNotExistWebhooks:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> dict[str, int]:
        new_created_count = 0
        exist_webhooks_ids = set(Webhook.objects.values_list("webhook_id", flat=True))
        webhooks = self.asana_api_client.get_webhooks(workspace_id=ATLAS_WORKSPACE_ID)
        for webhook_data in webhooks:
            if webhook_data["gid"] not in exist_webhooks_ids:
                Webhook.objects.create(
                    webhook_id=webhook_data["gid"],
                    resource_name=webhook_data["resource"].get("name", ""),
                    resource_type=webhook_data["resource"].get("resource_type", ""),
                    target=webhook_data["target"],
                )
                new_created_count += 1
        return {"new_created_count": new_created_count}
