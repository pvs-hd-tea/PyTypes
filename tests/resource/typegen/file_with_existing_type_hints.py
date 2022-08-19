class Clazz:
    def __init__(self):
        self.class_member = 5

    def change_value(self, parameter1: int, parameter2) -> None:
        local_variable = parameter1 == parameter2
        self.class_member = int(local_variable)
        return local_variable


def function(parameter):
    assert isinstance(parameter, Clazz)
