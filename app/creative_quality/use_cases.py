from creative_quality.models import Creative, Task
from creative_quality.services import CreativeService


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
