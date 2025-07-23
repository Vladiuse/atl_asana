from .models import AsanaWebhookRequestData, CompletedTask

SECTION_COMPLETE_ID = "1210393628043136"


def is_task_complete(event: dict, target_section: str) -> bool:
    return (
        event.get("action") == "added"
        and event.get("resource", {}).get("resource_type") == "task"
        and event.get("parent", {}).get("resource_type") == "section"
        and event.get("parent", {}).get("gid") == target_section
    )


def completed_task_creator(asana_webhook_model: AsanaWebhookRequestData) -> list[CompletedTask]:
    records = []
    for event in asana_webhook_model.events:
        if is_task_complete(event=event, target_section=asana_webhook_model.project.complete_section_id):
            completed_task = CompletedTask.objects.create(
                webhook=asana_webhook_model,
                event_data=event,
                task_id=event["resource"]["gid"],
                project=asana_webhook_model.project,
            )
            records.append(completed_task)

    return records
