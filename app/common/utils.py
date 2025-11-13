def normalize_multiline(text: str) -> str:
    lines = text.splitlines()
    cleaned = [line.lstrip() for line in lines]
    return "\n".join(cleaned).strip()
