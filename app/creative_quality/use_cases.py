from creative_quality.models import Creative, Task
from creative_quality.services import CreativeService, SendEstimationMessageService


class CreateCreativesForNewTasksUseCase:
    def __init__(self, creative_service: CreativeService):
        self.creative_service = creative_service

    def execute(self) -> dict:
        """
        Load task info and create Creative
        """
        new_tasks = Task.objects.needs_update()
        created_count = 0
        for task in new_tasks:
            creative = self.creative_service.create_creative(creative_task=task)
            if creative is not None:
                created_count += 1
        return {"created_count": created_count}


class CreativesOverDueForEstimateUseCase:
    """
    Change status of Creative if due estimate time
    """

    def execute(self) -> dict:
        creatives = Creative.objects.overdue_for_estimate()
        for creative in creatives:
            creative.mark_need_estimate()
        return {"count": len(creatives)}


class SendEstimationMessageUseCase:
    """
    Send estimation message if reach send time
    """
    def __init__(self, estimation_service: SendEstimationMessageService):
        self.estimation_service = estimation_service

    def execute(self) -> dict:
        creatives = Creative.objects.need_send_estimate_message().select_related("task")
        for creative in creatives:
            self.estimation_service.send_reminder(creative=creative)
        return {"count": len(creatives)}
