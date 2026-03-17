from dataclasses import dataclass
from typing import Callable

from .abstract import BaseWebhookAction


@dataclass
class WebhookActionInfo:
    name: str
    description: str
    webhook_handler_class: type[BaseWebhookAction]


WEBHOOK_ACTION_REGISTRY: dict[str, WebhookActionInfo] = {}


def register_webhook_action(
    name: str,
    description: str,
) -> Callable[[type[BaseWebhookAction]], type[BaseWebhookAction]]:
    def wrap(cls: type[BaseWebhookAction]) -> type[BaseWebhookAction]:
        if name in WEBHOOK_ACTION_REGISTRY:
            msg = f"Webhook handler name {name} already registered"
            raise RuntimeError(msg)
        sender_info = WebhookActionInfo(
            name=name,
            description=description,
            webhook_handler_class=cls,
        )
        WEBHOOK_ACTION_REGISTRY[name] = sender_info
        return cls

    return wrap
