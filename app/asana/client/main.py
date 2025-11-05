import json
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, NoReturn

import requests
from requests.exceptions import HTTPError, RequestException

from .exception import AsanaApiClientError, AsanaNotFoundError


def asana_error_handler(func: Callable) -> Callable:
    """Автоматическая обработка ошибок для методов AsanaApiClient"""

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:  # noqa: ANN401
        try:
            return func(self, *args, **kwargs)
        except (RequestException, HTTPError, json.JSONDecodeError) as error:
            self._handle_error(handler_name=func.__name__, error=error)

    return wrapper


class AsanaApiClient:
    API_ENDPOINT = "https://app.asana.com/api/1.0/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _handle_error(self, handler_name: str, error: Exception) -> NoReturn:
        if isinstance(error, HTTPError):
            msg = f"AsanaApiClient {handler_name}: {error.response.text}"
            response = error.response
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise AsanaNotFoundError(msg, response=response) from error
        elif isinstance(error, json.JSONDecodeError):
            msg = f"AsanaApiClient {handler_name}: Ошибка разбора JSON ответа"
            response = None
        else:
            msg = f"AsanaApiClient {handler_name}: Ошибка запроса клиента трекера, {error}"
            response = None
        raise AsanaApiClientError(msg, response=response) from error

    @asana_error_handler
    def get_user(self, user_id: int) -> dict:
        response = requests.get(f"{self.API_ENDPOINT}users/{user_id}", headers=self._auth_headers)
        response.raise_for_status()
        return response.json()["data"]

    @asana_error_handler
    def get_workspace_memberships_for_workspace(self, workspace_id: int) -> list:
        response = requests.get(
            f"{self.API_ENDPOINT}workspaces/{workspace_id}/workspace_memberships",
            headers=self._auth_headers,
            params={"limit": 99},
        )
        response.raise_for_status()
        return response.json()["data"]
