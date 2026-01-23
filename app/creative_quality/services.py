from dataclasses import dataclass
from datetime import timedelta

from asana.client import AsanaApiClient
from asana.client.exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError
from common import MessageRenderer
from constance import config
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from message_sender.client import AtlasMessageSender
from message_sender.client.exceptions import AtlasMessageSenderError

from .models import Creative, CreativeAdaptation, CreativeProjectSection, Task, TaskStatus


@dataclass
class CreativeProjectSectionService:
    asana_api_client: AsanaApiClient

    def update_additional_info(self, creative_project_section: CreativeProjectSection) -> None:
        """Update additional info.

        Raises:
             AsanaApiClientError: if cant get some data from asana

        """
        section_data = self.asana_api_client.get_section(section_id=creative_project_section.section_id)
        creative_project_section.section_name = section_data["name"]
        creative_project_section.project_name = section_data["project"]["name"]
        creative_project_section.save()

    def fetch_tasks_ids(self, creative_project_section: CreativeProjectSection) -> list[str]:
        section_tasks = self.asana_api_client.get_section_tasks(section_id=creative_project_section.section_id)
        return [task["gid"] for task in section_tasks]


@dataclass(frozen=True)
class CreativeSubTask:
    name: str


@dataclass(frozen=True)
class CreativeTaskData:
    assignee_id: str
    name: str
    bayer_code: str
    url: str
    work_url: str


class CreativeService:
    def __init__(self, asana_api_client: AsanaApiClient):
        self.asana_api_client = asana_api_client

    def _get_task_dto(self, creative_task: Task) -> CreativeTaskData:
        task_data = self.asana_api_client.get_task(task_id=creative_task.task_id)
        assignee_id = "" if task_data["assignee"] is None else task_data["assignee"]["gid"]
        task_name = task_data["name"]
        url = task_data["permalink_url"]
        bayer_code = ""
        work_url = ""
        for field in task_data.get("custom_fields", []):
            if field["name"] == config.DESIGN_TASK_BAYER_CUSTOM_FIELD_NAME:
                bayer_code = field.get("text_value", "")
                break
        for field in task_data.get("custom_fields", []):
            if field["name"] == config.DESIGN_TASK_LINK_ON_WORK_FIELD_NAME:
                work_url = field.get("text_value", "")
                break
        return CreativeTaskData(
            assignee_id=assignee_id,
            name=task_name,
            bayer_code=bayer_code,
            url=url,
            work_url=work_url,
        )

    def _get_sub_tasks(self, creative_task: Task) -> list[CreativeSubTask]:
        sub_tasks_data = self.asana_api_client.get_sub_tasks(task_id=creative_task.task_id)
        return [CreativeSubTask(name=sub_task["name"]) for sub_task in sub_tasks_data]

    def update_task(self, creative_task: Task, task_dto: CreativeTaskData, *, save: bool = True) -> Task:
        creative_task.assignee_id = task_dto.assignee_id
        creative_task.bayer_code = task_dto.bayer_code.strip().lower()
        creative_task.task_name = task_dto.name
        creative_task.url = task_dto.url
        creative_task.work_url = task_dto.work_url
        if save:
            creative_task.save()
        return creative_task

    def create_creative(self, creative_task: Task) -> Creative | None:
        try:
            task_dto = self._get_task_dto(creative_task=creative_task)
            sub_tasks = self._get_sub_tasks(creative_task=creative_task)
        except (AsanaNotFoundError, AsanaForbiddenError):
            creative_task.mark_deleted()
        except AsanaApiClientError:
            creative_task.mark_error_load_info()
        else:
            with transaction.atomic():
                creative_task = self.update_task(creative_task=creative_task, task_dto=task_dto, save=False)
                creative_task.status = TaskStatus.CREATED
                creative_task.save()
                need_rated_at = creative_task.created + timedelta(days=config.NEED_RATED_AT)
                creative = Creative.objects.create(task=creative_task, need_rated_at=need_rated_at)
                if len(sub_tasks) == 0:
                    sub_tasks = [CreativeSubTask(name=task_dto.name)]
                creative_adaptations_to_create = []
                for sub_task in sub_tasks:
                    creative_adaptation = CreativeAdaptation(
                        name=sub_task.name,
                        creative=creative,
                    )
                    creative_adaptations_to_create.append(creative_adaptation)
                CreativeAdaptation.objects.bulk_create(creative_adaptations_to_create)
                return creative
        return None

    def end_estimate(self, creative: Creative) -> None:
        creative.mark_rated()
        # make asana task complete
        try:
            self.mark_task_completed(task=creative.task)
        except AsanaApiClientError:
            from .tasks import mark_asana_task_completed_task

            mark_asana_task_completed_task.apply_async(  # type: ignore[attr-defined]
                kwargs={"task_pk": creative.task.pk},
                countdown=3600,
            )

    def mark_task_completed(self, task: Task) -> None:
        """Mark task completed.

        Raises:
             AsanaApiClientError

        """
        try:
            self.asana_api_client.mark_task_completed(task_id=task.task_id)
            task.is_completed = True
            task.save(update_fields=["is_completed"])
        except (AsanaNotFoundError, AsanaForbiddenError):
            task.mark_deleted()


class SendEstimationMessageService:
    message = """
    ✏️ Нужно оценить креатив:<br>
    Task: {{task_name}}<br>
    Estimate Link: {{estimate_url}}<br>
    """

    def __init__(self, message_sender: AtlasMessageSender, message_renderer: MessageRenderer):
        self.message_sender = message_sender
        self.message_renderer = message_renderer

    def send_reminder(self, creative: Creative) -> None:
        bayer_code = creative.task.bayer_code
        user_tag = bayer_code.lower()
        context = {
            "task_name": creative.task.task_name,
            "estimate_url": self._get_estimation_url(creative=creative),
        }
        message = self.message_renderer.render(template=self.message, context=context)
        try:
            self.message_sender.send_message_to_user(message=message, user_tag=user_tag)
        except AtlasMessageSenderError as error:
            creative.reminder_failure_count += 1
            if creative.reminder_failure_count >= config.SEND_REMINDER_TRY_COUNT:
                creative.mark_reminder_limit_reached(save=False)
            else:
                creative.next_reminder_at = timezone.now() + timedelta(hours=config.FAILURE_RETRY_INTERVAL)
            creative.reminder_fail_reason = str(error)
        else:
            creative.reminder_success_count += 1
            if creative.reminder_success_count >= config.SEND_REMINDER_TRY_COUNT:
                creative.mark_reminder_limit_reached(save=False)
            else:
                creative.next_reminder_at = timezone.now() + timedelta(hours=config.NEXT_SUCCESS_REMINDER_DELTA)
        creative.save()

    def _get_estimation_url(self, creative: Creative) -> str:
        return creative.get_estimate_url(domain=settings.DOMAIN)
