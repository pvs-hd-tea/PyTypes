class AClass:
    def __init__(self, a):
        self.aclass_attr = a # set attribute in class C, TYPE HINT!

    def set(self, another_c):
        another_c.ano_attr = self.aclass_attr # set attribute in class C, TYPE HINT!

class AnotherC:
    def __init__(self, a):
        self.ano_attr = a # set attribute in class C, TYPE HINT!

    def reset(self, a):
        a.ano_attr = -50  # set attribute in class C, TYPE HINT!

# Do not type hint, as it is not in the class C
def func_taking_aclass(aclass):
    v, aclass.aclass_attr = 10, 5  # set attribute in class C, DO NOT TYPE HINT!
    return v

def func_taking_anotherc(anotherc):
    anotherc.ano_attr, i = 10, -20  # set attribute in class AnotherC, DO NOT TYPE HINT!
    return i


def main():
    func_taking_aclass(AClass(5))
    func_taking_anotherc(AnotherC(36))
