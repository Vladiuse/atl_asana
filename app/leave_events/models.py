from datetime import datetime, timedelta
from turtle import Shape
from typing import Any

from common.message_renderer import render_message
from constance import config
from django.db import models, transaction
from django.utils import timezone
from message_sender.client import Handlers
from message_sender.models import ScheduledMessage
from django.db.models import QuerySet

TABLE_URL = "https://docs.google.com/spreadsheets/d/1bbo6WxBLGk24FeSRucCYkwuWu1cYafb_5XsVgBO1DnY/edit?gid=570923352#gid=570923352"
NOTIFICATION_MESSAGE = """
<b>Запланирован {{leave_type|lower}}</b> 📅<br>
{{supervisor_tag}}<br>
Сотрудник {{employee}} согласовал {{leave_type|lower}} в даты {{start_date}} - {{end_date}}<br>
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

REMIND_MESSAGE = """
<b>Начало {{leave_type|lower}}a ⏳</b><br>
{{supervisor_tag}}<br>
Сотрудник {{employee}} уходит в {{leave_type|lower}} через 2 недели<br>
Отпуск: {{start_date}} - {{end_date}}<br>
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""


class LeaveType(models.TextChoices):
    VACATION = "VACATION", "Отпуск"
    DAY_OFF = "DAY_OFF", "Отгул"


class LeaveStatus(models.TextChoices):
    PENDING = "pending", "Нужно согласовать"
    APPROVED = "approved", "Согласовано"
    DELETED = "deleted", "Удалено"


class LeaveNotificationQuerySet(models.QuerySet["LeaveNotification"]):
    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:  # noqa: ANN401
        _ = args, kwargs
        for obj in self:
            obj.delete()
        return len(self), {}


class LeaveNotificationManager(models.Manager):  # type: ignore[type-arg]
    def get_queryset(self) -> LeaveNotificationQuerySet:
        return LeaveNotificationQuerySet(self.model, using=self._db)

    def create(self, **kwargs: Any) -> "Leave":  # noqa: ANN401
        with transaction.atomic():
            leave: Leave = super().create(**kwargs)
            context = {
                "table_url": TABLE_URL,
                "leave_type": LeaveType(leave.type).label,
                "supervisor_tag": leave.supervisor_tag,
                "employee": leave.employee,
                "start_date": leave.start_date.strftime("%d.%m.%Y"),
                "end_date": leave.end_date.strftime("%d.%m.%Y"),
            }
            ScheduledMessage.objects.create(
                run_at=timezone.now() + timedelta(minutes=config.SEND_NOTIFICATION_DELAY),
                text=render_message(template=NOTIFICATION_MESSAGE, context=context),
                handler=Handlers.HR_VACATION.value,
                reference_id=f"leave-{leave.pk}",
            )

            run_at = datetime.combine(
                leave.start_date,
                timezone.localtime(timezone.now()).time(),
            ) - timedelta(days=config.SEND_REMINDER_DELAY)
            ScheduledMessage.objects.create(
                run_at=run_at,
                text=render_message(template=REMIND_MESSAGE, context=context),
                handler=Handlers.HR_VACATION.value,
                reference_id=f"leave-{leave.pk}",
            )
            return leave


class Leave(models.Model):
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

    @property
    def messages(self) -> QuerySet[ScheduledMessage]:
        return ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}")

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        ScheduledMessage.objects.filter(reference_id=f"leave-{self.pk}").delete()
        return super().delete(*args, **kwargs)

    def is_can_be_deleted(self) -> bool:
        return self.cancellable_until > timezone.now()
