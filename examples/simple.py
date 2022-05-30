import sys, os

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root))

from tracing import hook


def sample_compare_two_int_lists(list1, list2):
    if len(list1) != len(list2):
        return False

    for i, element1 in enumerate(list1):
        element2 = list2[i]
        are_elements_equal = sample_compare_integers(element1, element2)
        if not are_elements_equal:
            return False
    return True


def sample_compare_integers(value1, value2) -> bool:
    result = value1 == value2
    return result


def sample_get_two_variables_declared_in_one_line():
    variable1, variable2 = 1, "string"
    return variable1, variable2


def sample_convert_string_to_int(string_to_convert):
    try:
        integer = int(string_to_convert)
        return integer
    except ValueError:
        return None

@hook
def driver():
    sample_compare_two_int_lists([1, 2, 3], [4, 5, 6])
    sample_compare_integers(1, 2)
    sample_get_two_variables_declared_in_one_line()
    sample_convert_string_to_int("123")