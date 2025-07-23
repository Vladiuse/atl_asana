from requests.exceptions import HTTPError, RequestException
from retry import retry

from .exception import TableSenderError
from .request_sender import RequestsSender


class TableSender:
    URL = "https://script.google.com/macros/s/AKfycbw0D7XfahlxDXgetBhI24hicCvL839QVBD817JEu20LIgqKB71OpCbWUc6jSyCNzhopCg/exec"
    AVAILABLE_URL = [
        "add_new_asana_task",
        "add_task_tech",
    ]

    def __init__(self, request_sender: RequestsSender):
        self.request_sender = request_sender

    @retry(
        exceptions=(HTTPError, RequestException),
        delay=5,
        tries=2,
    )
    def _send_message(self, handler: str, data: dict) -> str:
        data = {
            "url": handler,
            "data": data,
        }
        return self.request_sender.request(
            url=self.URL,
            method="POST",
            json=data,
        )

    def send_message(self, handler: str, message: str) -> str:
        if handler not in self.AVAILABLE_URL:
            raise TypeError(f"Incorrect handler, allowed {self.AVAILABLE_URL}")
        try:
            return self._send_message(handler=handler, message=message)
        except (HTTPError, RequestException) as error:
            if isinstance(error, HTTPError):
                msg = (
                    f"Не удалось отправить сообщение: Code: {error.response.status_code}, Text: {error.response.text}"
                )
            else:
                msg = f"Не удалось отправить сообщение, {error}"
            raise TableSenderError(msg)
