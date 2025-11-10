from asana.client import AsanaApiClient


class AsanaCommentNotifierUseCase:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def execute(self) -> None:
        pass
