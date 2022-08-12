class C:
    def __init__(self):
        self.name = "Hello"


def f(c):
    c.name = "World"
    name = 1
    name, c.name = c.name, name
