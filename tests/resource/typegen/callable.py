def add(x, y):
    return x + y

class C:
    def __init__(self):
        self.a = 0

    def method(a, n, s):
        a.b = "string"
        a.c, d = True, 3.14
        e, a.b, C().a = \
            None, "string2", 5
        return bytes(f"{n} + {s}")

    def outer(self, b):
        def inner(i):
            self.a += self.a + i # Can access class members anyway!
            return self.a
        return inner(b)


# Do not type hint, as it is not in the class C
def method(b, n, s):
    return bytes(f"{n} + {s}")
