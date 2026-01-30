from datetime import datetime, timedelta
from typing import Any

from common.message_renderer import render_message
from django.db import models, transaction
from django.utils import timezone
from message_sender.models import ScheduledMessage
from message_sender.client import Handlers

TABLE_URL = "https://docs.google.com/spreadsheets/d/1bbo6WxBLGk24FeSRucCYkwuWu1cYafb_5XsVgBO1DnY/edit?gid=570923352#gid=570923352"
NOTIFICATION_MESSAGE = """
Запланирован отпуск  📅
{{supervisor_tag}}
Сотрудник {{employee}} согласовал {{leave_type}} в даты {{start_date}} - {{end_date}}
Таблица отпусков: {{table_url}}
"""

REMIND_MESSAGE = """
Начало отпуска ⏳
{{supervisor_tag}}
Сотрудник {{employee}} уходит в отпуска через 2 недели
Отпуск: {{start_date}} - {{end_date}}
Таблица отпусков: {{table_url}}
"""


class LeaveType(models.TextChoices):
    VACATION = "VACATION", "Отпуск"
    DAY_OFF = "DAY_OFF", "Отгул"


class LeaveNotificationManager(models.Manager):  # type: ignore[type-arg]
    def create(self, **kwargs: Any) -> "LeaveNotification":  # noqa: ANN401
        with transaction.atomic():
            leave:LeaveNotification = super().create(**kwargs)
            context = {
                "table_url": TABLE_URL,
                "supervisor_tag": leave.supervisor_tag,
                "employee": leave.employee,
                "start_date": leave.start_date.strftime("%d.%m.%Y"),
                "end_date": leave.end_date.strftime("%d.%m.%Y"),
            }
            ScheduledMessage.objects.create(
                run_at=timezone.now() + timedelta(minutes=5),
                text=render_message(template=NOTIFICATION_MESSAGE, context=context),
                handler=Handlers.HR_VACATION.value,
                reference_id=f"leave-{leave.pk}",
            )

            run_at = datetime.combine(
                leave.start_date,
                timezone.now().time(),
            ) - timedelta(weeks=2)
            ScheduledMessage.objects.create(
                run_at=run_at,
                text=render_message(template=REMIND_MESSAGE, context=context),
                handler=Handlers.HR_VACATION.value,
                reference_id=f"leave-{leave.pk}",
            )
            return leave


class LeaveNotification(models.Model):
    type = models.CharField(max_length=30, choices=LeaveType)
    employee = models.CharField(max_length=254)
    supervisor_tag = models.CharField(max_length=254)
    start_date = models.DateField()
    end_date = models.DateField()
    cancellable_until = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)

    objects = LeaveNotificationManager()

    class Meta:
        unique_together = ("employee", "start_date")

    def __str__(self) -> str:
        return f"{self.employee}:{self.start_date}"

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}").delete()
        return super().delete(*args, **kwargs)

    def is_can_be_deleted(self) -> bool:
        return self.cancellable_until > timezone.now()
