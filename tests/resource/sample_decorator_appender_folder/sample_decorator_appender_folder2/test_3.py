from tests.resource.sample_functions import sample_compare_two_int_lists  # type: ignore


def test_pass(  )   :
    assert True


def test_if_two_lists_contain_different_elements_true_is_returned():
    list1 = [1, 2, 4, 4]
    list2 = [1, 2, 3, 4]
    expected = False

    actual = sample_compare_two_int_lists(list1, list2)
    assert expected == actual