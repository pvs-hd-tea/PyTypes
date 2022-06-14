# This file is used to test if the test function collector works.
# type: ignore
from examples.simple import sample_compare_two_int_lists, sample_compare_integers, sample_convert_string_to_int


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


def test_if_two_lists_contain_same_elements_true_is_returned():
    list1 = [1, 2, 4, 4]
    list2 = [1, 2, 4, 4]
    expected = True

    actual = sample_compare_two_int_lists(list1, list2)
    assert expected == actual


def test_if_two_lists_contain_different_elements_true_is_returned():
    list1 = [1, 2, 4, 4]
    list2 = [1, 2, 3, 4]
    expected = False

    actual = sample_compare_two_int_lists(list1, list2)
    assert expected == actual