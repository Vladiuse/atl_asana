from dataclasses import dataclass


@dataclass
class AsanaNewCommentEvent:
    comment_id: int
    user_id: int
    task_id: int


def process_asana_comment_event(events_data: dict) -> list[AsanaNewCommentEvent]:
    result = []
    for event in events_data["events"]:
        event_dto = AsanaNewCommentEvent(
            comment_id=event["resource"]["gid"],
            user_id=event["user"]["gid"],
            task_id=event["parent"]["gid"],
        )
        result.append(event_dto)
    return result
