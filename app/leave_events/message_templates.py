# ruff: noqa: E501
PENDING_LEAVE_MESSAGE = """
<b>Запланирован {{leave.get_type_display|lower}} 📅</b><br>
@{{leave.supervisor_tag}}<br>
{%if leave.type == leave_type.VACATION%}
Сотрудник {{leave.employee}} планирует отпуск в даты {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}}<br>
{%else%}
Сотрудник {{leave.employee}} планирует отгул {{leave.start_date|date:"d.m.Y"}}<br>
{%endif%}

<b>Нужно согласование 🔔</b><br>

<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""

NOTIFICATION_FOR_EMPLOYEE_MESSAGE = """
<b>Согласован {{leave.get_type_display|lower}}</b> 📅<br>
{%if leave.type == leave_type.VACATION%}
Твой отпуск в даты {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}} согласован ✅
{%else%}
Твой отгул {{leave.start_date|date:"d.m.Y"}} согласован ✅
{%endif%}
"""

REMIND_MESSAGE = """
<b>Начало {{leave.get_type_display|lower}}a ⏳</b><br>
@{{leave.supervisor_tag}}<br>
Сотрудник {{leave.employee}} уходит в {{leave.get_type_display|lower}} через {{day_delta}} дней<br>
{%if leave.type == leave_type.VACATION%}
Отпуск: {{leave.start_date|date:"d.m.Y"}} - {{leave.end_date|date:"d.m.Y"}}<br>
{%else%}
Отгул: {{leave.start_date|date:"d.m.Y"}}<br>
{%endif%}
<a href="{{table_url}}">Таблица отпусков Atlas</a>
"""
