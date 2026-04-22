from datetime import date
from typing import Any

from .constants import AsanaResourceType
from .exception import FieldNotFoundError


def get_asana_profile_url_by_id(profile_id: str, workspace_id: str) -> str:
    return f"https://app.asana.com/1/{workspace_id}/profile/{profile_id}"


def is_task_sub_task(task_data: dict[str, Any]) -> bool:
    """Determine whether the task is a subtask."""
    parent = task_data["parent"]
    return parent is not None and parent["resource_type"] == AsanaResourceType.TASK


def get_field_value_from_task(
    field_name: str,
    task_data: dict[str, Any],
    default_value: str | None = None,
    *,
    raise_if_not_found: bool = False,
) -> str | None:
    """Return "text_value" of custom field of asana task."""
    for custom_field in task_data["custom_fields"]:
        if field_name == custom_field["name"]:
            return custom_field["text_value"]
    if raise_if_not_found:
        msg = f'Field "{field_name}" not found in asana task data'
        raise FieldNotFoundError(msg)
    return default_value


def get_date_field_value_from_task(
    field_name: str,
    task_data: dict[str, Any],
    default_value: date | None = None,
    *,
    raise_if_not_found: bool = False,
) -> date | None:
    """Return date of custom field of asana task."""
    for custom_field in task_data["custom_fields"]:
        if (
            field_name == custom_field["name"]
            and custom_field["type"] == "date"
            and custom_field["date_value"] is not None
        ):
            date_str = custom_field["date_value"]["date"]
            return date.fromisoformat(date_str)
    if raise_if_not_found:
        msg = f'Field "{field_name}" not found in asana task data'
        raise FieldNotFoundError(msg)
    return default_value


def clean_user_avatar_url(url: str) -> str:
    """Clean asana avatar url (remove query params).

    Example:
        https://asaba.com/cb1e4_128x128.png?e=1777479093&v=0&t=nvRV34_0m931d --> https://asaba.com/cb1e4_128x128.png

    """
    return  url.split("?")[0]
