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
<b>Запланирован {{leave.get_type_display|lower}} 📅</b>

{{leave.supervisor_tag}}<br>
{%if leave.type == leave_type.VACATION%}
Сотрудник {{leave.employee}} планирует отпуск в даты {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}}<br>
{%else%}
Сотрудник {{leave.employee}} планирует отгул {{leave.start_date|date:"d.m.Y"}}<br>
{%endif%}

<b>Нужно согласование 🔔</b><br>

<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

NOTIFICATION_MESSAGE = """
<b>Запланирован {{leave.get_type_display|lower}}</b> 📅<br>
{{leave.supervisor_tag}}<br>
{%if leave.type == leave_type.VACATION%}
Сотрудник {{leave.employee}} согласовал отпуск в даты {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}}<br>
{%else%}
Сотрудник {{leave.employee}} согласовал отгул {{leave.start_date|date:"d.m.Y"}}<br>
{%endif%}
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

REMIND_MESSAGE = """
<b>Начало {{leave.get_type_display|lower}}a ⏳</b><br>
{{leave.supervisor_tag}}<br>
Сотрудник {{leave.employee}} уходит в {{leave.get_type_display|lower}} через {{day_delta}} дней<br>
{%if leave.type == leave_type.VACATION%}
Отпуск: {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}}<br>
{%else%}
Отгул: {{leave.start_date|date:"d.m.Y"}}<br>
{%endif%}
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""
DAYS_IN_WEEK = 7


@dataclass
class LeaveData:
    start_date: date
    employee: str
    status: LeaveStatus
    type: LeaveType


class LeaveNotificationService:
    @property
    def handler(self) -> str:
        return config.MESSAGE_HANDLER

    def _create_notification_message(self, leave: Leave) -> None:
        context = {
            "leave": leave,
            "leave_type": LeaveType,
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

    def _create_remind_message(self, leave: Leave) -> None:
        now: datetime = timezone.localtime(timezone.now())
        today: date = now.date()
        days_until_leave = (leave.start_date - today).days
        if days_until_leave >= DAYS_IN_WEEK * 2:
            reminder_delay = 14
        elif days_until_leave >= DAYS_IN_WEEK:
            reminder_delay = 7
        else:
            reminder_delay = None
        if reminder_delay is not None:
            context = {
                "leave": leave,
                "leave_type": LeaveType,
                "day_delta": reminder_delay,
                "table_url": config.LEAVE_TABLE_URL,
            }
            run_at = datetime.combine(
                leave.start_date,
                now.time(),
            ) - timedelta(days=reminder_delay)
            text = render_message(template=REMIND_MESSAGE, context=context)
            ScheduledMessage.objects.create(
                run_at=run_at,
                text=text,
                handler=self.handler,
                reference_id=f"leave-{leave.pk}",
            )

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
            "leave_type": LeaveType,
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
        self._create_notification_message(leave=leave)
        self._create_remind_message(leave=leave)
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
