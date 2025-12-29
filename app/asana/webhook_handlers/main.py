from creative_quality.models import CreativeProjectSection, Task

from asana.models import AsanaWebhookRequestData

from .abstract import BaseWebhookHandler, WebhookHandlerResult
from .registry import register_webhook_handler


@register_webhook_handler(
    name="AddCreativeTaskForEstimation",
    description="Карточка с креативом добавлен в колонку для оценки креатива",
)
class CreativeTaskForEstimation(BaseWebhookHandler):
    def get_target_sections_ids(self) -> set[str]:
        return set(CreativeProjectSection.objects.values_list("section_id", flat=True))

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookHandlerResult:
        target_sections_ids = self.get_target_sections_ids()
        event_data = webhook_data.payload
        is_created = False
        for event in event_data["events"]:
            if self._is_target_event(event_data=event):
                section_id = event["parent"]["gid"]
                if section_id in target_sections_ids:
                    task_id = event["resource"]["gid"]
                    _, created = Task.objects.get_or_create(
                        task_id=task_id,
                        defaults={"task_id": task_id},
                    )
                    if created:
                        is_created = True
        return WebhookHandlerResult(is_success=True, is_target_event=is_created)

    def _is_target_event(self, event_data: dict) -> bool:
        # is task moved to section
        return (
            event_data.get("action") == "added"
            and event_data.get("resource", {}).get("resource_type") == "task"
            and event_data.get("parent", {}).get("resource_type") == "section"
        )
