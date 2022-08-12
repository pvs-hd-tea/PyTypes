from tests.resource.typegen.callable import C

def f(i: int) -> str:
    c = C()
    c.a: int = 10
    return f"{c.outer(i)}"

def another_one():
    a: int
    b: float
    a, b = 5, 2.0

    c: str = "Hello World"