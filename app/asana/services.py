import re

from django.db.models import QuerySet

from .constants import Position
from .models import AtlasAsanaUser


def get_user_profile_url_mention_map(asana_users: QuerySet[AtlasAsanaUser] | list[AtlasAsanaUser]) -> dict[str, str]:
    result = {}
    for user in asana_users:
        result.update(
            {
                user.profile_url: user.user_comment_mention,
            },
        )
    return result


def map_messenger_position_to_asana(messenger_position: str) -> Position | None:
    return {
        "bayer": Position.BUYER,
        "buyer": Position.BUYER,
        "farmer": Position.FARMER,
    }.get(messenger_position.lower())


class AsanaCommentPrettifier:
    def __init__(self, profile_urls_mention_map: dict[str, str]):
        self.profile_urls_mention_map = profile_urls_mention_map

    def _replace_asana_profile_urls_on_mention(self, text: str) -> str:
        for profile_url, mention in self.profile_urls_mention_map.items():
            text = text.replace(profile_url, mention)
        return text

    def _replace_links(self, text: str) -> str:
        url_pattern = re.compile(r"https?://[^\s]+")
        return url_pattern.sub("[link]", text)

    def prettify(self, comment_text: str) -> str:
        comment_text = self._replace_asana_profile_urls_on_mention(text=comment_text)
        return self._replace_links(text=comment_text)
