from dataclasses import asdict, dataclass, field
from typing import TypeAlias

from common.exception import AppExceptionError

from asana.models import AsanaWebhookRequestData, ProcessingStatus
from asana.webhook_handlers.abstract import WebhookHandlerResult
from asana.webhook_handlers.registry import WEBHOOK_HANDLER_REGISTRY, WebhookHandlerInfo

HandlerName: TypeAlias = str


@dataclass
class WebhookDispatcherResult:
    handler_results: dict[HandlerName, WebhookHandlerResult] = field(default_factory=dict)
    errors: dict[HandlerName, str] = field(default_factory=dict)


class WebhookDispatcher:
    def dispatch(self, webhook_data: AsanaWebhookRequestData) -> WebhookDispatcherResult:
        result = WebhookDispatcherResult()
        webhook = webhook_data.webhook
        handlers = webhook.handlers.all()
        if len(handlers) == 0:
            webhook_data.status = ProcessingStatus.NO_HANDLERS
            webhook_data.save(update_fields=["status"])
            return result
        for handler in handlers:
            handler_info: WebhookHandlerInfo | None = WEBHOOK_HANDLER_REGISTRY.get(handler.name)
            try:
                if not handler_info:
                    msg = f"Cant find webhook handler with name '{handler.name}'"
                    raise AppExceptionError(msg)
                handler_class = handler_info.webhook_handler_class
                handler_result: WebhookHandlerResult = handler_class().handle(webhook_data=webhook_data)
                result.handler_results[handler.name] = handler_result
            # need for isolate handlers if it raises error
            except Exception as exc:  # noqa: BLE001
                result.errors[handler.name] = str(exc)
        if not result.handler_results:
            status = ProcessingStatus.FAILED
        elif result.errors:
            status = ProcessingStatus.PARTIAL
        else:
            status = ProcessingStatus.SUCCESS
        webhook_data.additional_data = asdict(result)
        webhook_data.status = status
        webhook_data.save(update_fields=["additional_data", "status"])
        return result

    # for tests only
    def _get_registry_dict(self) -> dict:
        return WEBHOOK_HANDLER_REGISTRY
