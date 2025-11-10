import json
from enum import Enum

from django.conf import settings
from requests.exceptions import HTTPError, RequestException
from retry import retry

from common.request_sender import RequestsSender

from .exception import MessageSenderError


class Users(Enum):
    KVA = "kva_tech"
    DAV = "dav"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.name) for item in cls]


class MessageSender:
    URL = "https://atlasmainpanel.com/api/alert/custom"
    API_KEY = settings.DOMAIN_MESSAGE_API_KEY
    DOMAIN_HANDLER = "domain_check"
    KVA_USER = "kva_test"
    ALLOWED_HANDLERS = [DOMAIN_HANDLER, KVA_USER]

    def __init__(self, request_sender: RequestsSender):
        self.request_sender = request_sender

    @property
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.API_KEY}"}

    @retry(
        exceptions=(HTTPError, RequestException),
        delay=5,
        tries=2,
    )
    def _send_message(self, handler: str, message: str) -> str:
        data = {
            "title": handler,
            "text": message,
        }
        return self.request_sender.request(
            url=self.URL,
            method="POST",
            headers=self._auth_headers,
            json=data,
        )

    def send_message(self, handler: str, message: str) -> str:
        # if handler not in self.ALLOWED_HANDLERS:
        #     raise TypeError(f"Incorrect handler, allowed {self.ALLOWED_HANDLERS}")
        try:
            return self._send_message(handler=handler, message=message)
        except (HTTPError, RequestException) as error:
            if isinstance(error, HTTPError):
                msg = (
                    f"Не удалось отправить сообщение: Code: {error.response.status_code}, Text: {error.response.text}"
                )
            else:
                msg = f"Не удалось отправить сообщение, {error}"
            raise MessageSenderError(msg)

    def send_message_to_user(self, message: str, user_tags: list[str]) -> dict:
        data = {
            "text": message,
            "tags": user_tags,
        }
        response = self.request_sender.request(
            url=self.URL,
            method="POST",
            headers=self._auth_headers,
            json=data,
        )
        data = json.loads(response)
        if len(data["users"]) != len(user_tags):
            raise MessageSenderError("Число тегов юзеров и отправленных сообщений не совпадает")
        return data
