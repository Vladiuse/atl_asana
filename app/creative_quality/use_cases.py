import gspread
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from google.oauth2.service_account import Credentials
from gspread import Client
from message_sender.tasks import send_log_message_task

from creative_quality.creative_table import CreativeDto, CreativeGoogleTable
from creative_quality.models import Creative, CreativeGeoData, CreativeProjectSection, CreativeStatus, Task, TaskStatus
from creative_quality.services import CreativeProjectSectionService, CreativeService, SendEstimationMessageService


class CreateCreativesForNewTasksUseCase:
    def __init__(self, creative_service: CreativeService):
        self.creative_service = creative_service

    def execute(self) -> dict:
        """Load task info and create Creative."""
        new_tasks = Task.objects.needs_update()
        created_count = 0
        for task in new_tasks:
            creative = self.creative_service.create_creative(creative_task=task)
            if creative is not None:
                created_count += 1
        return {"created_count": created_count}


class CreativesOverDueForEstimateUseCase:
    """Change status of Creative if due estimate time."""

    def execute(self) -> dict:
        creatives = Creative.objects.overdue_for_estimate()
        for creative in creatives:
            creative.mark_need_estimate()
        return {"count": len(creatives)}


class SendEstimationMessageUseCase:
    """Send estimation message if reach send time."""

    def __init__(self, estimation_service: SendEstimationMessageService):
        self.estimation_service = estimation_service

    def execute(self) -> dict:
        creatives = Creative.objects.need_send_estimate_message().select_related("task")
        for creative in creatives:
            self.estimation_service.send_reminder(creative=creative)
        return {"count": len(creatives)}


class SendCreativesToGoogleSheetUseCase:
    def _convert_creative_to_dto(self, creative_geo_data: CreativeGeoData) -> CreativeDto:
        creative = creative_geo_data.creative
        task = creative.task
        return CreativeDto(
            assignee=task.get_assignee_display(),
            bayer_code=task.bayer_code,
            hold=creative_geo_data.hold,
            hook=creative_geo_data.hook,
            ctr=creative_geo_data.ctr,
            task_name=task.task_name,
            task_url=task.url,
            link_on_work=task.work_url,
            status=creative_geo_data.status,
            comment=creative_geo_data.comment,
            country=creative_geo_data.country.iso_code,
        )

    def _get_client(self) -> Client:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=scopes,
        )
        return gspread.authorize(credentials=credentials)

    def execute(self) -> dict:
        """Execute use case.

        Raises:
             gspread.GSpreadException

        """
        client = self._get_client()
        creatives_to_send = (
            Creative.objects.need_send_to_gsheet()
            .select_related("task")
            .prefetch_related("geo_data", "geo_data__country")
        )
        send_result: list[dict] = []
        for creative in creatives_to_send:
            creatives_geo_data_dto = [
                self._convert_creative_to_dto(creative_geo_data=creative_geo_data)
                for creative_geo_data in creative.geo_data.all()
            ]
            google_table = CreativeGoogleTable(client=client)
            result = google_table.add_creatives(creatives=creatives_geo_data_dto)
            send_result.append(dict(result))
            creative.gsheet_sent = True
            creative.save()
        return {"creatives_to_send": len(creatives_to_send), "send_result": send_result}

    def send_test_creative_to_table(self) -> dict:
        creative_dto = CreativeDto(
            country="XX",
            assignee="assignee",
            bayer_code="XXX",
            hold=1,
            hook=2,
            ctr=3,
            task_name="TASK NAME",
            task_url="url",
            link_on_work="link_on_work",
            status="STATUS",
            comment="comment text",
        )
        client = self._get_client()
        google_table = CreativeGoogleTable(client=client)
        creatives_dto = [creative_dto, creative_dto]
        result = google_table.add_creatives(creatives=creatives_dto)
        return dict(result)


class FetchMissingTasksUseCase:
    def __init__(self, creative_project_section_service: CreativeProjectSectionService):
        self.creative_project_section_service = creative_project_section_service

    def execute(self) -> dict[str, int]:
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
            message = f"⚠️ {self.__class__.__name__}:\n"
            f"Found new_found:{new_found} missing creatives tasks, errors: {with_errors}"
            send_log_message_task.delay(message=message)  # type: ignore[attr-defined]
        return {"new_found": new_found, "with_errors": with_errors}


class DataIntegrityCheckUseCase:
    def _check_tasks_full_data(self) -> None:
        tasks_qs = Task.objects.filter(status=TaskStatus.CREATED).filter(Q(assignee_id="") | Q(bayer_code=""))
        if tasks_qs.exists():
            tasks_ids = tasks_qs.values_list("task_id", flat=True)
            message = f"⚠️ {self.__class__.__name__}: Found tasks without required data: {tasks_ids}"
            send_log_message_task.delay(message=message)  # type: ignore[attr-defined]

    def _check_task_error_load_info(self) -> None:
        tasks_qs = Task.objects.error_load_info()
        if tasks_qs.exists():
            tasks_ids = tasks_qs.values_list("task_id", flat=True)
            message = f"⚠️ {self.__class__.__name__}: Found tasks cant load info: {tasks_ids}"
            send_log_message_task.delay(message=message)  # type: ignore[attr-defined]

    def _check_creatives_cant_send_message(self) -> None:
        creatives_qs = Creative.objects.filter(status=CreativeStatus.REMINDER_LIMIT_REACHED)
        if creatives_qs.exists():
            creatives_ids = creatives_qs.values_list("pk", flat=True)
            message = f"⚠️ {self.__class__.__name__}:\n"
            f"Found creatives with status {CreativeStatus.REMINDER_LIMIT_REACHED}: {creatives_ids}"
            send_log_message_task.delay(message=message)  # type: ignore[attr-defined]

    def execute(self) -> None:
        self._check_tasks_full_data()
        self._check_task_error_load_info()
        self._check_creatives_cant_send_message()
