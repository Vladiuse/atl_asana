class AppException(Exception):
    """Common application exception"""


class MessageSenderError(AppException):
    """MessageSenderError"""


class TableSenderError(AppException):
    """TableSenderError"""
