from dataclasses import dataclass

from asana.client import AsanaApiClient



@dataclass
class LoadAdditionalInfoForProjectIgnoredSection:
    asana_api_client: AsanaApiClient

    def load(self, project_ignored_section: ProjectIgnoredSection) -> None:
        """
        Raises:
             AsanaApiClientError: if cant get some data from asana
        """
        section_data = self.asana_api_client.get_section(project_ignored_section.section_id)
        project_ignored_section.section_name = section_data["name"]
        project_ignored_section.save()
