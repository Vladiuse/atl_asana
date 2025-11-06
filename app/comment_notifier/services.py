from dataclasses import dataclass

from .models import AsanaComment


class ProcessAsanaNewCommentEvent:
    @dataclass
    class AsanaNewCommentEvent:
        comment_id: int
        user_id: int
        task_id: int

    @dataclass
    class Result:
        created_comments_count: int
        comments: list["ProcessAsanaNewCommentEvent.AsanaNewCommentEvent"]

    def _event_to_comment_dto(self, events_data: dict) -> list[AsanaNewCommentEvent]:
        result = []
        for event in events_data["events"]:
            event_dto = ProcessAsanaNewCommentEvent.AsanaNewCommentEvent(
                comment_id=event["resource"]["gid"],
                user_id=event["user"]["gid"],
                task_id=event["parent"]["gid"],
            )
            result.append(event_dto)
        return result

    def process(self, events_data: dict) -> Result:
        asana_comments_dto = self._event_to_comment_dto(events_data=events_data)
        for comment_dto in asana_comments_dto:
            AsanaComment.objects.create(
                comment_id=comment_dto.comment_id,
                user_id=comment_dto.user_id,
                task_id=comment_dto.task_id,
            )
        return ProcessAsanaNewCommentEvent.Result(
            created_comments_count=len(asana_comments_dto),
            comments=asana_comments_dto,
        )
