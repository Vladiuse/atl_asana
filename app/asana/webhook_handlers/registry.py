from dataclasses import dataclass
from typing import Callable

from .abstract import BaseWebhookHandler


@dataclass
class WebhookHandlerInfo:
    name: str
    description: str
    sender: type[BaseWebhookHandler]


WEBHOOK_HANDLER_REGISTRY: dict[str, WebhookHandlerInfo] = {}


def register_webhook_handler(
    name: str, description: str,
) -> Callable[[type[BaseWebhookHandler]], type[BaseWebhookHandler]]:
    def wrap(cls: type[BaseWebhookHandler]) -> type[BaseWebhookHandler]:
        if name in WEBHOOK_HANDLER_REGISTRY:
            raise RuntimeError(f"Webhook handler name {name} already registered")
        sender_info = WebhookHandlerInfo(
            name=name,
            description=description,
            sender=cls,
        )
        WEBHOOK_HANDLER_REGISTRY[name] = sender_info
        return cls

    return wrap
