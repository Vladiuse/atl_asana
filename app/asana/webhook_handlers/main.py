from asana.models import AsanaWebhookRequestData

from .abstract import BaseWebhookHandler, WebhookHandlerResult
from .registry import register_webhook_handler
from creative_quality.models import Task


@register_webhook_handler(
    name="TEst1",
    description="some desc 1",
)
class TestOneHandler(BaseWebhookHandler):
    def handle(self, webhook_data: AsanaWebhookRequestData) -> None:
        pass


@register_webhook_handler(
    name="AddCreativeTaskForEstimation",
    description="Таск с креативом для оценки",
)
class CreativeTaskForEstimation(BaseWebhookHandler):

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookHandlerResult:
        event_data = webhook_data.payload
        is_created = False
        for event in event_data["events"]:
            if self._is_target_event(event_data=event):
                task_id = event["resource"]["gid"]
                obj, created = Task.objects.get_or_create(
                    task_id=task_id,
                    defaults={"task_id": task_id},
                )
                if created:
                    is_created = True
        return WebhookHandlerResult(is_success=True, is_target_event=is_created)


    def _is_target_event(self, event_data: dict) -> bool:
        return (event_data.get("action") == "added"
            and event_data.get("resource", {}).get("resource_type") == "task"
            and event_data.get("parent", {}).get("resource_type") == "section")