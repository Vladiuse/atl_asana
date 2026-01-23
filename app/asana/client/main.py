import json
import logging
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, NoReturn, TypeVar

import requests
from requests.exceptions import HTTPError, RequestException

from .exception import AsanaApiClientError, AsanaForbiddenError, AsanaNotFoundError

ReturnType = TypeVar("ReturnType")


def asana_error_handler(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
    """Автоматическая обработка ошибок для методов AsanaApiClient."""

    @wraps(func)
    def wrapper(self: "AsanaApiClient", *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        try:
            return func(self, *args, **kwargs)
        except (RequestException, HTTPError, json.JSONDecodeError) as error:
            self._handle_error(handler_name=func.__name__, error=error)

    return wrapper


class AsanaApiClient:
    API_ENDPOINT = "https://app.asana.com/api/1.0/"
    DEFAULT_REQUEST_TIMEOUT = 6

    def __init__(self, api_key: str, timeout: int | None = None):
        self.api_key = api_key
        self.timeout = timeout if timeout else self.DEFAULT_REQUEST_TIMEOUT

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _handle_error(self, handler_name: str, error: Exception) -> NoReturn:
        if isinstance(error, HTTPError):
            msg = f"AsanaApiClient {handler_name}: {error.response.text}"
            response = error.response
            logging.info("Response status code: %s", response.status_code)
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise AsanaNotFoundError(msg, response=response) from error
            if response.status_code == HTTPStatus.FORBIDDEN:
                raise AsanaForbiddenError(msg, response=response) from error
        if isinstance(error, json.JSONDecodeError):
            msg = f"AsanaApiClient {handler_name}: Ошибка разбора JSON ответа"
            response = None
        else:
            msg = f"AsanaApiClient {handler_name}: Ошибка запроса клиента трекера, {error}"
            response = None
        raise AsanaApiClientError(msg, response=response) from error

    @asana_error_handler
    def get_user(self, user_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{self.API_ENDPOINT}users/{user_id}",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_workspace_membership(self, membership_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{self.API_ENDPOINT}workspace_memberships/{membership_id}",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_workspace_memberships_for_workspace(self, workspace_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}workspaces/{workspace_id}/workspace_memberships",
            headers=self._auth_headers,
            timeout=self.timeout,
            params={"limit": 99},
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_comment(self, comment_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{self.API_ENDPOINT}stories/{comment_id}",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_stories_from_task(self, task_id: int, opt_fields: list[str] | None = None) -> list[dict[str, Any]]:
        if opt_fields is None:
            opt_fields = []
        response = requests.get(
            f"{self.API_ENDPOINT}tasks/{task_id}/stories",
            headers=self._auth_headers,
            params={"opt_fields": opt_fields},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_comments_from_task(self, task_id: int, opt_fields: list[str] | None = None) -> list[dict[str, Any]]:
        stories = self.get_stories_from_task(task_id=task_id, opt_fields=opt_fields)
        return [story for story in stories if story["resource_subtype"] == "comment_added"]

    @asana_error_handler
    def get_task(self, task_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{self.API_ENDPOINT}tasks/{task_id}",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def update_task(self, task_id: int, data: dict[str, Any], opt_fields: list[str] | None = None) -> dict[str, Any]:
        if opt_fields is None:
            opt_fields = []
        data = {"data": data}
        response = requests.put(
            f"{self.API_ENDPOINT}tasks/{task_id}",
            headers=self._auth_headers,
            json=data,
            params={"opt_fields": opt_fields},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    def mark_task_completed(self, task_id: str) -> dict[str, Any]:
        return self.update_task(task_id=task_id, data={"completed": True}, opt_fields=["completed", "name"])

    @asana_error_handler
    def get_sub_tasks(self, task_id: str) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}tasks/{task_id}/subtasks",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_workspace_memberships_for_user(self, user_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}users/{user_id}/workspace_memberships",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_webhooks(self, workspace_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}webhooks",
            headers=self._auth_headers,
            params={"workspace": workspace_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_project_sections(self, project_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}projects/{project_id}/sections",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_section_tasks(self, section_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.API_ENDPOINT}sections/{section_id}/tasks",
            headers=self._auth_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        if "next_page" in response.text:
            msg = "get_section_tasks have 'next_page' param in response"
            raise AsanaApiClientError(msg)
        return response.json()["data"]

    @asana_error_handler
    def get_project(self, project_id: int, opt_fields: list[str] | None = None) -> dict[str, Any]:
        if opt_fields is None:
            opt_fields = []
        response = requests.get(
            f"{self.API_ENDPOINT}projects/{project_id}",
            headers=self._auth_headers,
            params={"opt_fields": opt_fields},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_section(self, section_id: int, opt_fields: list[str] | None = None) -> dict[str, Any]:
        if opt_fields is None:
            opt_fields = []
        response = requests.get(
            f"{self.API_ENDPOINT}sections/{section_id}",
            headers=self._auth_headers,
            params={"opt_fields": opt_fields},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["data"]
