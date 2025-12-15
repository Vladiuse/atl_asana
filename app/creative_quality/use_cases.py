import gspread
from django.conf import settings
from django.db import IntegrityError
from google.oauth2.service_account import Credentials
from message_sender.tasks import send_log_message_task

from creative_quality.creative_table import CreativeDto, CreativeGoogleTable
from creative_quality.models import Creative, CreativeProjectSection, Task
from creative_quality.services import CreativeProjectSectionService, CreativeService, SendEstimationMessageService


class CreateCreativesForNewTasksUseCase:
    def __init__(self, creative_service: CreativeService):
        self.creative_service = creative_service

    def execute(self) -> dict:
        """
        Load task info and create Creative
        """
        new_tasks = Task.objects.needs_update()
        created_count = 0
        for task in new_tasks:
            creative = self.creative_service.create_creative(creative_task=task)
            if creative is not None:
                created_count += 1
        return {"created_count": created_count}


class CreativesOverDueForEstimateUseCase:
    """
    Change status of Creative if due estimate time
    """

    def execute(self) -> dict:
        creatives = Creative.objects.overdue_for_estimate()
        for creative in creatives:
            creative.mark_need_estimate()
        return {"count": len(creatives)}


class SendEstimationMessageUseCase:
    """
    Send estimation message if reach send time
    """

    def __init__(self, estimation_service: SendEstimationMessageService):
        self.estimation_service = estimation_service

    def execute(self) -> dict:
        creatives = Creative.objects.need_send_estimate_message().select_related("task")
        for creative in creatives:
            self.estimation_service.send_reminder(creative=creative)
        return {"count": len(creatives)}


class SendCreativesToGoogleSheetUseCase:
    def _convert_creative_to_dto(self, creative: Creative) -> CreativeDto:
        return CreativeDto(
            assignee=creative.task.get_assignee_display(),
            bayer_code=creative.task.bayer_code,
            hold=creative.hold,
            hook=creative.hook,
            ctr=creative.ctr,
            task_name=creative.task.task_name,
            task_url=creative.task.task_url,
            status=creative.status,
            comment=creative.comment,
        )

    def execute(self) -> dict:
        """
        Raises:
             gspread.GSpreadException
        """
        creatives_to_send = Creative.objects.need_send_to_gsheet().select_related("task")
        creatives_dto = [self._convert_creative_to_dto(creative=creative) for creative in creatives_to_send]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=scopes,
        )
        client = gspread.authorize(credentials=creds)
        google_table = CreativeGoogleTable(client=client)
        result = google_table.add_creatives(creatives=creatives_dto)
        return dict(result)


class FetchMissingTasksUseCase:
    def __init__(self, creative_project_section_service: CreativeProjectSectionService):
        self.creative_project_section_service = creative_project_section_service

    def execute(self) -> dict:
        sections = CreativeProjectSection.objects.all()
        new_found = []
        with_errors = []
        for section in sections:
            exist_task_ids = set(Task.objects.values_list("task_id", flat=True))
            section_task_ids = self.creative_project_section_service.fetch_tasks_ids(
                creative_project_section=section,
            )
            for task_id in section_task_ids:
                if task_id not in exist_task_ids:
                    try:
                        Task.objects.create(task_id=task_id)
                        new_found.append(task_id)
                    except IntegrityError:
                        with_errors.append(task_id)
        if any([new_found, with_errors]):
            message = f"{self.__class__.__name__}: Found {len(new_found)} missing creatives taks"
            send_log_message_task.delay(message=message)
        return {"new_found": new_found, "with_errors": with_errors}
