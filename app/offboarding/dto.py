from dataclasses import dataclass
from datetime import date


@dataclass
class TaskData:
    fio: str
    position: str
    tag: str
    url: str
    fired_date: date
