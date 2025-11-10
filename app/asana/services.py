from .models import AtlasUser


def prettify_asana_comment_text_with_mentions(text: str) -> str:
    asana_users = AtlasUser.objects.all()
    for user in asana_users:
        text = text.replace(user.profile_url, user.user_comment_mention)
    return text
