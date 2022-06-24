import typing


def compare_two_lists(list1, list2):
    if len(list1) != len(list2):
        return False

    for i, element1 in enumerate(list1):
        element2 = list2[i]
        are_elements_equal = element1 == element2
        if not are_elements_equal:
            return False
    return True


def does_list_contain_elements_of_one_type(list1: list):
    if len(list1) == 0:
        return True

    type_to_compare = None

    for element in list1:
        if not type_to_compare:
            type_to_compare = type(element)

        elif not isinstance(element, type_to_compare):
            return False

    return True


def check_and_get_index_and_element_if_element_in_collection(list1 : list, element_to_check: typing.Any):
    for i, element in enumerate(list1):
        if element == element_to_check:
            return True, i, element
    return False, -1, None


def create_set_from(collection) -> set:
    return set(collection)


def test_if_list_contains_elements_of_one_type_true_is_returned():
    list1 = [1, 5, 12, -2, 0, -100]
    list2 = []
    list3 = ["a", "b", "c", "d"]
    set1 = set(list1)

    assert does_list_contain_elements_of_one_type(list1)
    assert does_list_contain_elements_of_one_type(list2)
    assert does_list_contain_elements_of_one_type(list3)
    assert does_list_contain_elements_of_one_type(set1)


def test_if_list_contains_elements_of_multiple_types_false_is_returned():
    list1 = [None, 6, "a"]
    list2 = [10, 3, 8, -5.0, 2]
    list3 = [[], None]
    set1 = set(list1)

    assert not does_list_contain_elements_of_one_type(list1)
    assert not does_list_contain_elements_of_one_type(list2)
    assert not does_list_contain_elements_of_one_type(list3)
    assert not does_list_contain_elements_of_one_type(set1)


def test_if_two_lists_contain_same_elements_true_is_returned():
    list1 = [1, 2, 4, 4]
    list2 = [1, 2, 4, 4]
    expected = True

    actual = compare_two_lists(list1, list2)
    assert expected == actual


def test_if_two_lists_contain_different_elements_true_is_returned():
    list1 = [1, 2, 4, 4]
    list2 = [1, 2, 3, 4]
    expected = False

    actual = compare_two_lists(list1, list2)
    assert expected == actual


def test_if_element_in_list_then_correct_values_are_returned():
    list1 = [None, 5, "a", "b"]
    bool1, index1, element1 = check_and_get_index_and_element_if_element_in_collection(list1, None)
    bool2, index2, element2 = check_and_get_index_and_element_if_element_in_collection(list1, 5)
    bool3, index3, element3 = check_and_get_index_and_element_if_element_in_collection(list1, "a")

    assert bool1 and bool2 and bool3
    assert index1 == 0 and index2 == 1 and index3 == 2
    assert element1 is None and element2 == 5 and element3 == "a"


def test_if_element_not_in_list_then_correct_values_are_returned():
    list1 = [None, 5, "a", "b"]
    bool1, index1, element1 = check_and_get_index_and_element_if_element_in_collection(list1, 4)
    bool2, index2, element2 = check_and_get_index_and_element_if_element_in_collection(list1, "c")

    assert bool1 == bool2 == False
    assert index1 == index2 == -1
    assert element1 == element2 == None


def test_if_set_is_created_then_it_contains_same_elements():
    list1 = [None, 6, "a"]
    list2 = [10, 3, 8, -5.0, 2]
    list4 = ["a", "b", "c", "d"]

    assert(compare_two_lists(list1, create_set_from(list1)))