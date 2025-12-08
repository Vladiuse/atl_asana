from dataclasses import dataclass

from asana.client import AsanaApiClient
from .models import AsanaWebhookProject

@dataclass
class LoadAdditionalInfoForWebhookProject:
    asana_api_client: AsanaApiClient

    def load(self, webhook_project: AsanaWebhookProject) -> None:
        project_data = self.asana_api_client.get_project(
            project_id=webhook_project.project_id,
            opt_fields=["name", "permalink_url"],
        )
        webhook_project.project_name = project_data["name"]
        webhook_project.project_url = project_data["permalink_url"]
        webhook_project.save()