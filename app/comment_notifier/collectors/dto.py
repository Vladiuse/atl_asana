from dataclasses import dataclass
from typing import Any

from asana.models import AtlasAsanaUser

from comment_notifier.models import AsanaComment


@dataclass
class CommentDto:
    comment_model: AsanaComment
    comment_data: dict[str, Any]
    task_data: dict[str, Any]
    pretty_comment_text: str
    mentions_profile_ids: list[str]
    mention_users: list[AtlasAsanaUser]
    profile_url_not_found_in_db: list[str]

    @property
    def has_mention(self) -> bool:
        return bool(self.mention_users)
