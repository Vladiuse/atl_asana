from dataclasses import dataclass


@dataclass
class TaskData:
    fio: str
    position: str
    tag: str
    url: str
