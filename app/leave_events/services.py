from dataclasses import dataclass
from datetime import date

from .models import LeaveStatus, LeaveType

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


@dataclass
class LeaveData:
    start_date: date
    employee: str
    status: LeaveStatus
    type: LeaveType


class LeaveNotificationService:
    def need_agreed(self, leave_data: LeaveData) -> None:
        pass

    def approved(self, leave_data: LeaveData) -> None:
        pass

    def delete(self, leave_data: LeaveData) -> None:
        pass

    def process_google_data(self, leave_data: LeaveData) -> None:
        handlers_by_status = {
            LeaveStatus.PENDING: self.need_agreed,
            LeaveStatus.APPROVED: self.approved,
            LeaveStatus.DELETED: self.delete,
        }
        handler = handlers_by_status[leave_data.status]
        handler(leave_data=leave_data)
