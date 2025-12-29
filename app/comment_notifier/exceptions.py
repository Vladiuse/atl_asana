from common.exception import AppExceptionError


class NoSenderClassInProjectError(AppExceptionError):
    """No set sender class on asana project."""
