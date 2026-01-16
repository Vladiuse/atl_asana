from requests import Response


class MessageSenderError(Exception):
    """Common client error."""

    def __init__(self, message: str, response: Response | None = None) -> None:
        super().__init__(message)
        self.response = response
