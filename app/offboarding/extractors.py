from typing import Any

from asana.utils import get_field_value_from_task

from .dto import TaskData
from .exceptions import OffboardingAppError


def extract_offboarding_task_data(task_data: dict[str, Any]) -> TaskData:
    """Get offboarding task data.

    Raises:
        OffboardingAppError: if task dont have full data.

    """
    fio = get_field_value_from_task(field_name="ФИО", task_data=task_data)
    tag = get_field_value_from_task(field_name="ТЭГ", task_data=task_data)
    position = get_field_value_from_task(field_name="Должность", task_data=task_data)
    url = task_data["permalink_url"]
    if not all([fio, tag, position]):
        raise OffboardingAppError("Not all required fields are filled")
    assert fio is not None  #  noqa: S101
    assert tag is not None  #  noqa: S101
    assert position is not None  #  noqa: S101
    return TaskData(fio=fio, position=position, tag=tag, url=url)
