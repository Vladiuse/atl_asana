from dataclasses import dataclass


@dataclass
class CommentSendMessageResult:
    is_send: bool
    messages: list[str | dict | None]
