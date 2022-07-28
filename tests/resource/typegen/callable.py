def add(x, y):
    return x + y

class C:
    def method(a, n, s):
        return bytes(f"{n} + {s}")


# Do not type hint, as it is not in the class C
def method(b, n, s):
    return bytes(f"{n} + {s}")
