from dataclasses import dataclass

from asana.client import AsanaApiClient
from .models import CreativeProjectSection


@dataclass
class LoadAdditionalInfoForCreativeProjectSection:
    asana_api_client: AsanaApiClient

    def load(self, creative_project_section: CreativeProjectSection) -> None:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        section_data = self.asana_api_client.get_section(creative_project_section.section_id)
        creative_project_section.section_name = section_data["name"]
        creative_project_section.project_name = section_data["project"]["name"]
        creative_project_section.save()
