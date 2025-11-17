from common.exception import AppException


class CantNotify(AppException):
    """Some reason cant send message"""
