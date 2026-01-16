from dataclasses import dataclass


@dataclass(frozen=True)
class UserData:
    name: str
    email: str | None
    role: str
    tag: str | None
    telegram: str
    username: str
