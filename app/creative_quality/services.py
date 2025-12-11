from dataclasses import dataclass
from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from constance import config

from .models import Creative, CreativeProjectSection, Task, TaskStatus


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




@dataclass
class UpdateTaskInfoService:
    asana_api_client: AsanaApiClient

    @dataclass
    class TaskData:
        assignee_id: str
        name: str
        bayer_code: str
        url: str

    asana_api_client: AsanaApiClient

    def _get_task_dto(self, task_data: dict) -> TaskData:
        """
        Raises:
             AsanaApiClientError
        """
        assignee_id = task_data.get("assignee", {}).get("gid", "")
        task_name = task_data["name"]
        url = task_data["permalink_url"]
        bayer_code = ""
        for field in task_data.get("custom_fields", []):
            if field["name"] == config.DESIGN_TASK_BAER_CUSTOM_FIELD_NAME:
                bayer_code = field.get("text_value", "")
                break
        return self.TaskData(
            assignee_id=assignee_id,
            name=task_name,
            bayer_code=bayer_code,
            url=url,
        )

    def update(self, creative_task: Task) -> Task:
        try:
            task_data = self.asana_api_client.get_task(task_id=creative_task.task_id)
            task_dto = self._get_task_dto(task_data=task_data)
            creative_task.assignee_id = task_dto.assignee_id
            creative_task.bayer_code = task_dto.bayer_code
            creative_task.task_name = task_dto.name
            creative_task.url = task_dto.url
            creative_task.status = TaskStatus.CREATED
            creative_task.save()
        except (AsanaNotFoundError, AsanaForbiddenError):
            creative_task.mark_deleted()
        except AsanaApiClientError:
            creative_task.status = TaskStatus.ERROR_LOAD_INFO
            creative_task.save()
        return creative_task


@dataclass
class CreateCreativeService:

    def __init__(self,asan_api_client: AsanaApiClient):
        self.asan_api_client = asan_api_client
        self.update_service = UpdateTaskInfoService(asana_api_client=asan_api_client)

    def create(self, creative_task: Task) -> None:
        creative_task = self.update_service.update(creative_task=creative_task)
        if creative_task.status == TaskStatus.CREATED:
            need_rated_at = creative_task.created + timedelta(days=config.NEED_RATED_AT)
            Creative.objects.create(task=creative_task, need_rated_at=need_rated_at)
