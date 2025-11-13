import re


USER_PROFILE_LINK_PATTERN = re.compile(r"https://app\.asana\.com/\d+/profile/(\d+)")


def extract_user_profile_id_from_text(text: str) -> list[int]:
    matches = re.findall(USER_PROFILE_LINK_PATTERN, text)
    return [int(m) for m in matches]
