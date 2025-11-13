from .models import AtlasUser


def prettify_asana_comment_text_with_mentions(text: str) -> str:
    asana_users = AtlasUser.objects.all()
    for user in asana_users:
        text = text.replace(user.profile_url, user.user_comment_mention)
    return text

class AsanaCommentPrettifier:

    def __init__(self, profile_urls_mention_map: dict[str, str]):
        self.profile_urls_mention_map = profile_urls_mention_map

    def prettify_comment(self, comment_text: str) -> str:
        for profile_url, mention in self.profile_urls_mention_map.items():
            comment_text = comment_text.replace(profile_url, mention)
        return comment_text