from abc import ABC, abstractmethod
from dataclasses import dataclass

from asana.models import AsanaWebhookRequestData


@dataclass(frozen=True)
class WebhookHandlerResult:
    is_target_event: bool
    is_success: bool
    error: str | None = None


class BaseWebhookHandler(ABC):
    @abstractmethod
    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookHandlerResult:
        pass
