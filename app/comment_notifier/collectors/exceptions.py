from common.exception import AppExceptionError


class CommentDeletedError(AppExceptionError):
    """Raised when a comment or its parent task has been deleted or is no longer accessible."""
