import json
from enum import Enum
from functools import cached_property, wraps
from typing import Any, Callable, NoReturn, TypeVar

import requests
from requests.exceptions import HTTPError, RequestException

from .exceptions import MessageSenderError
from .models import UserData

ReturnType = TypeVar("ReturnType")

REQUEST_TIMEOUT = 6


def error_handler(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
    @wraps(func)
    def wrapper(self: AtlasMessageSender, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        try:
            return func(self, *args, **kwargs)
        except (RequestException, HTTPError, json.JSONDecodeError) as error:
            self._handle_error(handler_name=func.__name__, error=error)

    return wrapper


class Handlers(Enum):
    DOMAIN_HANDLER = "domain_check"
    KVA_USER = "kva_test"
    FARM_GROUP = "asana_farm_comments"


class AtlasMessageSender:
    def __init__(self, host: str, api_key: str):
        self.host = host
        self.api_key = api_key
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    def _handle_error(self, handler_name: str, error: Exception) -> NoReturn:
        if isinstance(error, HTTPError):
            msg = f"{MessageSenderError.__class__.__name__} {handler_name}: {error.response.text}"
            raise MessageSenderError(msg, response=error.response) from error
        if isinstance(error, json.JSONDecodeError):
            msg = f"{MessageSenderError.__class__.__name__} {handler_name}: Ошибка разбора JSON ответа"
        else:
            msg = f"{MessageSenderError.__class__.__name__} {handler_name}: Ошибка запроса клиента, {error}"
        raise MessageSenderError(msg, response=None) from error

    @cached_property
    def base_url(self) -> str:
        return f"https://{self.host}/api"

    def send_message(
        self,
        handler: Handlers,
        message: str,
        timeout: int = REQUEST_TIMEOUT,
    ) -> dict[str, str | list[str]]:
        """Send message by handler.

        Response Example:
            {"text": "test", "users": [], "groups": []}

        """
        data = {
            "title": handler.value,
            "text": message,
        }
        url = f"{self.base_url}/alert/custom"
        response = self.session.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def send_message_to_users(
        self,
        message: str,
        user_tags: list[str],
        timeout: int = REQUEST_TIMEOUT,
        *,
        require_all: bool = True,
    ) -> dict[str, str | list[str]]:
        """Send message by user tags.

        Response Example:
            {'groups': [], 'text': '123', 'users': []}
        """
        data = {
            "text": message,
            "tags": user_tags,
        }
        url = f"{self.base_url}/alert/custom"
        response = self.session.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        response_data = json.loads(response.text)
        if require_all and len(response_data["users"]) != len(user_tags):
            msg = f"Число тегов юзеров и отправленных сообщений не совпадает. {user_tags}, ответ {data}"
            raise MessageSenderError(msg)
        return response_data

    def send_message_to_user(
        self,
        message: str,
        user_tag: str,
        timeout: int = REQUEST_TIMEOUT,
        *,
        require_all: bool = True,
    ) -> dict[str, str | list[str]]:
        return self.send_message_to_users(
            message=message,
            user_tags=[user_tag],
            timeout=timeout,
            require_all=require_all,
        )

    def send_log_message(self, message: str) -> dict[str, str | list[str]]:
        return self.send_message(handler=Handlers.KVA_USER, message=message)

    def users(self) -> list[UserData]:
        url = f"{self.base_url}/users"
        response = self.session.get(url)
        response.raise_for_status()
        response_data = response.json().get("result", {}).get("users")
        if response_data is None:
            msg = "Not found users data in response"
            raise MessageSenderError(message=msg, response=response)
        users = []
        for user_data in response_data:
            user = UserData(
                name=user_data["name"],
                email=user_data.get("email"),
                role=user_data["role"],
                tag=user_data.get("tag"),
                telegram=user_data["telegram"],
                username=user_data["username"],
            )
            users.append(user)
        return users
