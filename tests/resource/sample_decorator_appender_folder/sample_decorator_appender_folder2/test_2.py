from tests.resource.sample_functions import sample_convert_string_to_int, sample_compare_two_int_lists  # type: ignore


def test_pass   (      )  :
    assert True


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