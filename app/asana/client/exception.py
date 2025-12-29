from common.exception import AppExceptionError
from requests import Response


class AsanaApiClientError(AppExceptionError):
    """Common client error."""

    def __init__(self, message: str, response: Response | None = None) -> None:
        super().__init__(message)
        self.response = response


class AsanaNotFoundError(AsanaApiClientError):
    """404 Not Found."""


class AsanaForbiddenError(AsanaApiClientError):
    """403 Forbidden."""
