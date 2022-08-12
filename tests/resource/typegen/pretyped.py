class C:
    def __init__(self) -> None:
        self.a = 5

    def m(self, i) -> int:
        return self.a + i

def f(i: int) -> str:
    c: C = C()
    c.a = 10
    return f"{c.m(i)}"

def another_one():
    a: int
    b: float
    a, b = 5, 2.0

    c: str = "Hello World"