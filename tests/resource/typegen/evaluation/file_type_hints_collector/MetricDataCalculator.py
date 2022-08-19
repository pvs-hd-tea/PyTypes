import typing


class A:
    def __init__(self, integer: int):
        self.a: int | None = integer
        b: bool = False
        self.c: typing.Optional[str] = "string"
