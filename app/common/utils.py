import textwrap


def normalize_multiline(text: str) -> str:
    return textwrap.dedent(text).strip()
