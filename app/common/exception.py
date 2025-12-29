class AppExceptionError(Exception):
    """Common application exception."""


class MessageSenderError(AppExceptionError):
    """MessageSenderError."""


class TableSenderError(AppExceptionError):
    """TableSenderError."""
