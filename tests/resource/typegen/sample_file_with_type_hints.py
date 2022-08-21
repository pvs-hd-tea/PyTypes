class A:
    def __init__(self):
        self.a: float = 0.2

    def a(self, b: int) -> str:
        c: bool = True
        b: int; b += 1
        return "string"


def check_instance(a: A) -> bool:
    return isinstance(a, A)