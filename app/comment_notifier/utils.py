import re

USER_PROFILE_LINK_PATTERN = re.compile(r"https://app\.asana\.com/(?:1|0)/\d+/profile/(\d+)")


def extract_user_profile_id_from_text(text: str) -> list[str]:
    matches = re.findall(USER_PROFILE_LINK_PATTERN, text)
    return list(matches)
