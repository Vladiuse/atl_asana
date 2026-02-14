from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from common.message_renderer import render_message
from constance import config
from django.utils import timezone
from message_sender.client import Handlers
from message_sender.models import ScheduledMessage

from .models import Leave, LeaveStatus, LeaveType

PENDING_LEAVE_MESSAGE = """
<b>Запланирован отпуск 📅</b>

{{leave.supervisor_tag}}<br>
{%if leave.type == leave_type.VACATION%}
Сотрудник {{leave.employee}} планирует отпуск в даты {{leave.start_date}} - {{leave.end_date}}<br>
{%else%}
Сотрудник {{leave.employee}} планирует отгул {{leave.start_date}}<br>
{%endif%}

<b>Нужно согласование 🔔</b><br>

<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

NOTIFICATION_MESSAGE = """
<b>Запланирован {{leave.type|lower}}</b> 📅<br>
{{leave.supervisor_tag}}<br>
{%if leave.type == leave_type.VACATION%}
Сотрудник {{leave.employee}} согласовал отпуск в даты {{leave.start_date}} - {{leave.end_date}}<br>
{%else%}
Сотрудник {{leave.employee}} согласовал отгул {{leave.start_date}}<br>
{%endif%}
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

REMIND_MESSAGE = """
<b>Начало {{leave.type|lower}}a ⏳</b><br>
{{leave.supervisor_tag}}<br>
Сотрудник {{leave.employee}} уходит в {{leave.type|lower}} через 2 недели<br>
{%if leave.type == leave_type.VACATION%}
Отпуск: {{leave.start_date}} - {{leave.end_date}}<br>
{%else%}
Отгул: {{leave.start_date}}<br>
{%endif%}
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""


@dataclass
class LeaveData:
    start_date: date
    employee: str
    status: LeaveStatus
    type: LeaveType


class LeaveNotificationService:

    @property
    def handler(self) -> str:
        return Handlers.HR_VACATION.value

    def _need_agreed(self, leave_data: dict[str, Any]) -> Leave:
        leave, created = Leave.objects.update_or_create(
            employee=leave_data.pop("employee"),
            start_date=leave_data.pop("start_date"),
            defaults=leave_data,
        )
        if not created:
            leave.messages.delete()
        context = {
            "leave": leave,
            "table_url": config.LEAVE_TABLE_URL,
        }
        text = render_message(template=PENDING_LEAVE_MESSAGE, context=context)
        run_at = timezone.now() + timedelta(minutes=config.SEND_NOTIFICATION_DELAY)
        ScheduledMessage.objects.create(
            run_at=run_at,
            text=text,
            handler=self.handler,
            reference_id=f"leave-{leave.pk}",
        )
        return leave

    def _approved(self, leave_data: dict[str, Any]) -> Leave:
        leave = Leave.objects.get(
            employee=leave_data.pop("employee"),
            start_date=leave_data.pop("start_date"),
        )
        context = {
            "leave": leave,
            "table_url": config.LEAVE_TABLE_URL,
        }
        run_at = timezone.now() + timedelta(minutes=config.SEND_NOTIFICATION_DELAY)
        text = render_message(template=NOTIFICATION_MESSAGE, context=context)
        ScheduledMessage.objects.create(
                run_at=run_at,
                text=text,
                handler=self.handler,
                reference_id=f"leave-{leave.pk}",
            )

        run_at = datetime.combine(
            leave.start_date,
            timezone.localtime(timezone.now()).time(),
        ) - timedelta(days=config.SEND_REMINDER_DELAY)
        text = render_message(template=REMIND_MESSAGE, context=context)
        ScheduledMessage.objects.create(
            run_at=run_at,
            text=text,
            handler=self.handler,
            reference_id=f"leave-{leave.pk}",
        )
        leave.status = LeaveStatus.APPROVED
        leave.save()
        return leave

    def _delete(self, leave_data: dict[str, Any]) -> Leave:
        leave = Leave.objects.get(
            employee=leave_data.pop("employee"),
            start_date=leave_data.pop("start_date"),
        )
        leave.messages.delete()
        leave.delete()
        return leave

    def process_google_data(self, leave_data: dict[str, Any]) -> Leave:
        handlers_by_status = {
            LeaveStatus.PENDING: self._need_agreed,
            LeaveStatus.APPROVED: self._approved,
            LeaveStatus.DELETED: self._delete,
        }
        handler = handlers_by_status[leave_data["status"]]
        return handler(leave_data=leave_data)
