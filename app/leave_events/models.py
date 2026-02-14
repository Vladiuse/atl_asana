from datetime import datetime, timedelta
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


class LeaveQuerySet(models.QuerySet["Leave"]):
    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # noqa: ANN401
        _ = args, kwargs
        count = 0
        for obj in self:
            obj.delete()
            count += 1
        return count, {}


class LeaveManager(models.Manager.from_queryset(LeaveQuerySet)):  # type: ignore[misc]
    pass


class Leave(models.Model):
    type = models.CharField(max_length=30, choices=LeaveType)
    employee = models.CharField(max_length=254)
    supervisor_tag = models.CharField(max_length=254)
    start_date = models.DateField()
    end_date = models.DateField()
    created = models.DateTimeField(auto_now_add=True)

    objects = LeaveManager()

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
