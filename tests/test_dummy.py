def add(x, y):
    '''Sample function used for testing. Adds two numbers and returns its sum.'''
    z = x + y
    return z


def test_if_add_is_called_with_two_numbers_sum_is_returned():
    argument1 = 5
    argument2 = 16
    expected = 21

    actual = add(argument1, argument2)

    assert expected == actual