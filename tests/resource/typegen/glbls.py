from tracing import decorators

exists_outside_of_all_scopes = False


def f():
    not_a_global = "Hello"
    exists_outside_of_all_scopes = 5  # This is a local variable!

    global sneaky_inside_scope
    sneaky_inside_scope = True


def g():
    # This should induce a union type in BOTH functions
    global sneaky_inside_scope
    sneaky_inside_scope = "TypeChange"


def h():
    # Reference existing global
    global exists_outside_of_all_scopes
    exists_outside_of_all_scopes = 5


@decorators.trace
def main():
    # False
    print(exists_outside_of_all_scopes)
    f()

    # False True
    print(exists_outside_of_all_scopes, sneaky_inside_scope)

    # False TypeChange
    g()
    print(exists_outside_of_all_scopes, sneaky_inside_scope)

    # 5 TypeChange
    h()
    print(exists_outside_of_all_scopes, sneaky_inside_scope)


if __name__ == "__main__":
    main()
