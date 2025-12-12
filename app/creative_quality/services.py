from dataclasses import dataclass
from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from common import MessageRenderer
from common.exception import MessageSenderError
from common.message_sender import MessageSender, UserTag
from constance import config
from django.conf import settings
from django.utils import timezone

from .models import Creative, CreativeProjectSection, Task, TaskStatus


@dataclass
class CreativeProjectSectionService:
    asana_api_client: AsanaApiClient

    def update_additional_info(self, creative_project_section: CreativeProjectSection) -> None:
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

        assignee_id = "" if task_data["assignee"] is None else task_data.get("assignee", {}).get("gid", "")
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

    def mark_completed(self, task: Task) -> None:
        """
        Raises:
             AsanaApiClientError
        """
        try:
            self.asana_api_client.mark_task_completed(task_id=task.task_id)
            task.is_completed = True
            task.save(update_fields=["is_completed"])
        except (AsanaNotFoundError, AsanaForbiddenError):
            task.mark_deleted()


class CreateCreativeService:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client
        self.update_service = UpdateTaskInfoService(asana_api_client=asana_api_client)

    def create(self, creative_task: Task) -> None:
        creative_task = self.update_service.update(creative_task=creative_task)
        if creative_task.status == TaskStatus.CREATED:
            need_rated_at = creative_task.created + timedelta(days=config.NEED_RATED_AT)
            Creative.objects.create(task=creative_task, need_rated_at=need_rated_at)


@dataclass(frozen=True)
class CreativeEstimationData:
    comment: str
    hook: int
    hold: int
    ctr: int
    need_complete_task: bool


class CreativeService:
    def __init__(self, asan_api_client: AsanaApiClient):
        self.asan_api_client = asan_api_client
        self.update_service = UpdateTaskInfoService(asana_api_client=asan_api_client)

    def estimate(self, creative: Creative, estimate_data: CreativeEstimationData) -> None:
        creative.hook = estimate_data.hook
        creative.hold = estimate_data.hold
        creative.crt = estimate_data.ctr
        creative.comment = estimate_data.comment
        creative.mark_rated()
        # make asana task complete
        if estimate_data.need_complete_task is True:
            try:
                self.update_service.mark_completed(task=creative.task)
            except AsanaApiClientError:
                from .tasks import mark_asana_task_completed_task

                mark_asana_task_completed_task.apply_async(
                    kwargs={"task_pk": creative.task.pk},
                    countdown=3600,
                )


class SendEstimationMessageService:
    message = """
    Нужно оценить креатив:<br>
    Task: {{task_url}}<br>
    Estimate Link: {{estimate_url}}<br>
    """

    def __init__(self, message_sender: MessageSender, message_renderer: MessageRenderer) -> None:
        self.message_sender = message_sender
        self.message_renderer = message_renderer

    def send_reminder(self, creative: Creative) -> None:
        try:
            bayer_code = creative.task.bayer_code
            if bayer_code == "":
                raise ValueError(f"Empty baer code in creative: {creative}")
            user_tag = UserTag(bayer_code)
            context = {
                "task_url": creative.task.url,
                "estimate_url": self._get_estimation_url(creative=creative),
            }
            message = self.message_renderer.render(template=self.message, context=context)
            self.message_sender.send_message_to_user(message=message, user_tags=[user_tag])
            creative.reminder_success_count += 1
            if creative.reminder_success_count >= config.SEND_REMINDER_TRY_COUNT:
                creative.mark_reminder_limit_reached(save=False)
            else:
                creative.next_reminder_at = timezone.now() + timedelta(hours=config.NEXT_SUCCESS_REMINDER_DELTA)
        except (ValueError, MessageSenderError) as error:
            creative.reminder_failure_count += 1
            if creative.reminder_success_count >= config.SEND_REMINDER_TRY_COUNT:
                creative.mark_reminder_limit_reached(save=False)
            else:
                creative.next_reminder_at = timezone.now() + timedelta(hours=config.FAILURE_RETRY_INTERVAL)
            creative.reminder_fail_reason = str(error)
        creative.save()

    def _get_estimation_url(self, creative: Creative) -> str:
        return creative.get_estimate_url(domain=settings.DOMAIN)
