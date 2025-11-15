from dataclasses import dataclass

from asana.models import AtlasUser

from comment_notifier.models import AsanaComment


@dataclass
class CommentDto:
    comment_model: AsanaComment
    comment_data: dict
    task_data: dict
    pretty_comment_text: str
    mentions_profile_ids: list[int]
    mention_users: list[AtlasUser]
    profile_url_not_found_in_db: list[str]

    @property
    def has_mention(self) -> bool:
        return bool(self.mention_users)
