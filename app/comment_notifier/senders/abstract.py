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

    def _normalize_message(self, message: str) -> str:
        return normalize_multiline(message)
