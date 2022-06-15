from tests.resource.sample_functions import sample_compare_integers  # type: ignore


def test_pass():
    assert True


# These are tests only used to validate the generated trace data.
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
