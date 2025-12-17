from dataclasses import dataclass
from typing import Callable

from .abstract import BaseCommentSender


@dataclass
class SenderInfo:
    name: str
    description: str
    sender: type[BaseCommentSender]


SENDERS_REGISTRY: dict[str, SenderInfo] = {}


def register_sender(name: str, description: str) -> Callable[[type[BaseCommentSender]], type[BaseCommentSender]]:
    def wrap(cls: type[BaseCommentSender]) -> type[BaseCommentSender]:
        if name in SENDERS_REGISTRY:
            raise RuntimeError(f"Sender name {name} already registered")
        sender_info = SenderInfo(
            name=name,
            description=description,
            sender=cls,
        )
        SENDERS_REGISTRY[name] = sender_info
        return cls

    return wrap
