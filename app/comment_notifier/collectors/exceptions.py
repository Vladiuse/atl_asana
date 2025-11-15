from common.exception import AppException


class CommentDeleted(AppException):
        """Raised when a comment or its parent task has been deleted or is no longer accessible."""