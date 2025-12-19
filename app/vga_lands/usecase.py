from common import MessageSender, RequestsSender, TableSender
from common.exception import TableSenderError

from .models import AsanaWebhookRequestData, CompletedTask
from .services import completed_task_creator

message_sender = MessageSender(request_sender=RequestsSender())
table_sender = TableSender(request_sender=RequestsSender())


class ProcessAsanaWebhookUseCase:
    def execute(self, asana_webhook: AsanaWebhookRequestData) -> list:
        created: list[CompletedTask] = completed_task_creator(asana_webhook_model=asana_webhook)
        asana_webhook.is_target_event = len(created) != 0
        asana_webhook.save()

        for completed_task in created:
            data = {
                "task_id": completed_task.task_id,
            }
            try:
                response_text = table_sender.send_message(handler=completed_task.project.table_url, data=data)
                completed_task.response_text = response_text
                completed_task.is_send_in_table = True
                completed_task.save()
            except TableSenderError as error:
                message_sender.send_message(handler="kva_test", message=str(error))
                completed_task.is_send_in_table = False
                completed_task.error_text = str(error)
                completed_task.save()
                message = f"Error add task {completed_task.task_id}: {error}"
                message_sender.send_message(handler="kva_test", message=message)
        return created
