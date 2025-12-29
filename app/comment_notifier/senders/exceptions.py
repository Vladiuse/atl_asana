from common.exception import AppExceptionError


class CantNotifyError(AppExceptionError):
    """Some reason cant send message."""
