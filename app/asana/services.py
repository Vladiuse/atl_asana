import re

from django.db.models import QuerySet

from .models import AtlasUser


def get_user_profile_url_mention_map(asana_users: QuerySet[AtlasUser] | list[AtlasUser]) -> dict[str, str]:
    result = {}
    for user in asana_users:
        result.update(
            {
                user.profile_url: user.user_comment_mention,
            },
        )
    return result


class AsanaCommentPrettifier:
    def __init__(self, profile_urls_mention_map: dict[str, str]):
        self.profile_urls_mention_map = profile_urls_mention_map

    def _replace_asana_profile_urls_on_mention(self, text) -> str:
        for profile_url, mention in self.profile_urls_mention_map.items():
            text = text.replace(profile_url, mention)
        return text

    def _replace_links(self, text: str) -> str:
        url_pattern = re.compile(r"https?://[^\s]+")
        return url_pattern.sub("[link]", text)

    def prettify(self, comment_text: str) -> str:
        comment_text = self._replace_asana_profile_urls_on_mention(text=comment_text)
        return self._replace_links(text=comment_text)
