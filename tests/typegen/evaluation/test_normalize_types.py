from typegen.evaluation.normalize_types import normalize_type


def test_union_normalized_returns_correct_values():
    values_to_test = [
        ["str", "str"],
        ["typing.Union[typing.Union[str, int], typing.Optional[float]]", "None | float | int | str"],
        ["object | None | Optional[list[str]] | typing.Any", "None | list[str] | object | typing.Any"],
        ["typing.Optional[typing.Union[str, float]] | Union[list[list[typing.Union[float | int, str]]] | typing.Union[int, str, str | None]]",
         "None | float | int | list[list[float | int | str]] | str"],
        ["dict[typing.Optional[str], dict[bool | list[list[str]], Union[int, str | object]]]",
         "dict[None | str, dict[bool | list[list[str]], int | object | str]]"]
    ]

    for input_expected_pair in values_to_test:
        input = input_expected_pair[0]
        expected = input_expected_pair[1]

        actual = normalize_type(input)
        print("Actual: " + actual)
        print("Expected: " + expected)
        assert actual == expected
