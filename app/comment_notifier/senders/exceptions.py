from common.exception import AppException


class CantNotify(AppException):
    def __init__(self, msg: str, *, comment_id: str) -> None:
        super().__init__(msg)
        self.comment_id: str = comment_id
