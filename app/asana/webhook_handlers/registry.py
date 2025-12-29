from dataclasses import dataclass
from typing import Callable

from .abstract import BaseWebhookHandler


@dataclass
class WebhookHandlerInfo:
    name: str
    description: str
    webhook_handler_class: type[BaseWebhookHandler]


WEBHOOK_HANDLER_REGISTRY: dict[str, WebhookHandlerInfo] = {}


def register_webhook_handler(
    name: str,
    description: str,
) -> Callable[[type[BaseWebhookHandler]], type[BaseWebhookHandler]]:
    def wrap(cls: type[BaseWebhookHandler]) -> type[BaseWebhookHandler]:
        if name in WEBHOOK_HANDLER_REGISTRY:
            msg = f"Webhook handler name {name} already registered"
            raise RuntimeError(msg)
        sender_info = WebhookHandlerInfo(
            name=name,
            description=description,
            webhook_handler_class=cls,
        )
        WEBHOOK_HANDLER_REGISTRY[name] = sender_info
        return cls

    return wrap
