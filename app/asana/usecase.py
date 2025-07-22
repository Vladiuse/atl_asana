from .services import completed_task_creator
from .models import AsanaWebhookRequestData, CompletedTask
from common import MessageSender, RequestsSender


message_sender = MessageSender(request_sender=RequestsSender())


class ProcessAsanaWebhookUseCase:

    def execute(self, asana_webhook: AsanaWebhookRequestData) -> list:
        created: list[CompletedTask] = completed_task_creator(asana_webhook_model=asana_webhook)
        if created:
            created_tasks = [task.task_id for task in created]
            message = f"Completed Tasks: {created_tasks}"
            message_sender.send_message(handler="kva_test", message=message)
        return created

