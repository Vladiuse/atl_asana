from common import MessageSender, RequestsSender

from .models import AsanaWebhookRequestData, CompletedTask
from .services import completed_task_creator

message_sender = MessageSender(request_sender=RequestsSender())


class ProcessAsanaWebhookUseCase:
    def execute(self, asana_webhook: AsanaWebhookRequestData) -> list:
        created: list[CompletedTask] = completed_task_creator(asana_webhook_model=asana_webhook)
        if created:
            created_tasks = [task.task_id for task in created]
            message = f"Completed Tasks: {created_tasks}"
            message_sender.send_message(handler="kva_test", message=message)
        asana_webhook.is_target_event = len(created) != 0
        asana_webhook.save()
        return created
