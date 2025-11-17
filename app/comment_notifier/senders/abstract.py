from abc import ABC, abstractmethod

from common.utils import normalize_multiline

from comment_notifier.collectors.dto import CommentDto

from .dto import CommentSendMessageResult


class BaseCommentSender(ABC):
    def __init__(self, message_sender):
        self.message_sender = message_sender

    @abstractmethod
    def notify(self, comment_dto: CommentDto) -> CommentSendMessageResult:
        pass

    def _send_log_cant_notify(self, comment_dto: CommentDto, reason: str) -> None:
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
              ⚠️ Cant send message
              Reason: {reason}
              Comment Id: {comment_dto.comment_model.comment_id}
              Task url: {task_url}
          """
        message = self._normalize_message(message)
        return self.message_sender.send_log_message(message=message)

    def _normalize_message(self, message: str) -> str:
        return normalize_multiline(message)
