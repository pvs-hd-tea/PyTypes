import pytest


class BaseClass:
    def __init__(self, integer):
        self.integer = integer


class SubClass1(BaseClass):
    def __init__(self, integer):
        super().__init__(integer)


class SubClass2(BaseClass):
    def __init__(self, integer):
        super().__init__(integer)


def is_integer_positive(instance: BaseClass) -> bool:
    if not isinstance(instance, BaseClass):
        raise TypeError

    return instance.integer > 0


def test_if_is_integer_positive_receives_invalid_arguments_error_is_raised():
    with pytest.raises(TypeError):
        is_integer_positive(None)
        is_integer_positive(True)
        is_integer_positive(1)
        is_integer_positive("string")


def test_if_is_integer_of_instance_is_positive_correct_value_is_returned():
    assert is_integer_positive(BaseClass(1))
    assert is_integer_positive(SubClass1(2))
    assert is_integer_positive(SubClass2(3))

    assert not is_integer_positive(BaseClass(0))
    assert not is_integer_positive(SubClass1(-1))
    assert not is_integer_positive(SubClass2(-2))
