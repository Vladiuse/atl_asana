from dataclasses import asdict

from common.exception import AppException

from asana.models import AsanaWebhookRequestData, ProcessingStatus
from asana.webhook_handlers.abstract import WebhookHandlerResult
from asana.webhook_handlers.registry import WEBHOOK_HANDLER_REGISTRY, WebhookHandlerInfo


class WebhookDispatcher:
    def dispatch(self, webhook_data: AsanaWebhookRequestData) -> None:
        webhook = webhook_data.webhook
        handler_results: dict[str, dict] = {}
        errors: dict[str, str] = {}
        for handler in webhook.handlers.all():
            handler_info: WebhookHandlerInfo = WEBHOOK_HANDLER_REGISTRY.get(handler.name)
            try:
                if not handler_info:
                    raise AppException(f"Cant find webhook handler with name '{handler.name}'")
                handler_class = handler_info.webhook_handler_class
                handler_result: WebhookHandlerResult = handler_class().handle(webhook_data=webhook_data)
                handler_results[handler_info.name] = asdict(handler_result)
            except Exception as exc:  # noqa: BLE001
                errors[handler.name] = str(exc)
        if not handler_results:
            status = ProcessingStatus.FAILED
        elif errors:
            status = ProcessingStatus.PARTIAL
        else:
            status = ProcessingStatus.SUCCESS
        webhook_data.additional_data = {
            "errors": errors,
            "handler_results": handler_results,
        }
        webhook_data.status = status
        webhook_data.save(update_fields=["additional_data", "status"])
