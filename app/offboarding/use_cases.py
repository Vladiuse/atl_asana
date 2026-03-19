from django.utils import timezone
from message_sender.tasks import send_log_message_task

from .exceptions import OffboardingAppError
from .models import OffboardingTask
from .services import NotifyOffboardingCreateTaskService, OffboardingFinanceNotifierService


class NotifyCreatedTasksUseCase:
    def __init__(self, notify_service: NotifyOffboardingCreateTaskService):
        self.notify_service = notify_service

    def execute(self) -> None:
        tasks = OffboardingTask.objects.filter(
            status=OffboardingTask.Status.ACTIVE,
            notified_created=False,
            notified_created_at__lt=timezone.now(),
        )
        for task in tasks:
            try:
                self.notify_service.notify(task=task)
            except OffboardingAppError as error:
                msg = f"⚠️ Cant process offboarding asana task, id - {task.asana_task_id}\n{error}"
                send_log_message_task.delay(message=msg)  # type: ignore[attr-defined]


class NotifyIfNeedPayRollUseCase:
    def __init__(self, notify_service: OffboardingFinanceNotifierService):
        self.notify_service = notify_service

    def execute(self) -> None:
        tasks = OffboardingTask.objects.filter(status=OffboardingTask.Status.ACTIVE, notified_need_payroll=False)
        for task in tasks:
            try:
                self.notify_service.notify(task=task)
            except OffboardingAppError as error:
                msg = f"⚠️ Cant process offboarding asana task, id - {task.asana_task_id}\n{error}"
                send_log_message_task.delay(message=msg)  # type: ignore[attr-defined]
