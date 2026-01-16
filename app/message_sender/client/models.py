from dataclasses import dataclass


@dataclass
class User:
    name: str
    email: str | None
    role: str
    tag: str | None
    telegram: str
    username: str
