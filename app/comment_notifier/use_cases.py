from asana.client import AsanaApiClient
from asana.constants import SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID, SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID


class AsanaCommentNotifierUseCase:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> None:
        pass


class FetchMissingProjectCommentsUseCase:
    DIV_PROJECT_IGNORED_SECTIONS = [SOURCE_DIV_PROBLEMS_REQUESTS_COMPLETE_SECTION_ID]

    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def _project_active_section_ids(self) -> list[int]:
        result = []
        sections = self.asana_api_client.get_project_sections(project_id=SOURCE_DIV_PROBLEMS_REQUESTS_PROJECT_ID)
        for section_data in sections:
            if section_data["gid"] not in self.DIV_PROJECT_IGNORED_SECTIONS:
                result.append(section_data["gid"])
        return result

    def execute(self) -> None:
        sections = self._project_active_section_ids()
        print(sections)
