def sample_compare_integers(value1: int, value2: int) -> bool:
    result = value1 == value2
    return result


def sample_get_two_variables_declared_in_one_line() -> tuple[int, str]:
    variable1, variable2 = 1, "string"
    return variable1, variable2


def sample_convert_string_to_int(string_to_convert: str) -> int | None:
    try:
        integer = int(string_to_convert)
        return integer
    except ValueError:
        return None


def test_if_two_integers_are_equal_true_is_returned():
    int1 = 10
    int2 = 10
    expected = True

    actual = sample_compare_integers(int1, int2)

    assert expected == actual


def test_if_two_integers_are_not_equal_true_is_returned():
    int1 = 10
    int2 = 15
    expected = False

    actual = sample_compare_integers(int1, int2)

    assert expected == actual


def test_if_string_is_converted_to_int_the_number_matches_with_expected():
    string = "10"
    expected = 10

    actual = sample_convert_string_to_int(string)
    assert expected == actual


