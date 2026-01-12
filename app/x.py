from dataclasses import dataclass
from functools import cached_property


@dataclass
class A:
    some: str | None = None


def test(x: str) -> str:
    return x


a = A(some=None)
test(x=a.some)


class Test:
    def __str__(self) -> str:
        return "1"

    @cached_property
    def test(self) -> None:
        pass

