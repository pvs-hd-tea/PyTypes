from typegen.evaluation.normalize_unions import union_normalized


def test_union_normalized_returns_correct_values():
    values_to_test = [
        ["str", "str"],
        ["typing.Union[typing.Union[str, int], typing.Optional[float]]", "None | float | int | str"],
        ["object | None | Optional[list[str]] | typing.Any", "None | list[str] | object | typing.Any"],
        ["typing.Optional[typing.Union[str, float]] | Union[list[list[typing.Union[float | int, str]]] | typing.Union[int, str, str | None]]",
         "None | float | int | list[list[typing.Union[float|int,str]]] | str"]
    ]

    for input_expected_pair in values_to_test:
        input = input_expected_pair[0]
        expected = input_expected_pair[1]

        actual = union_normalized(input)
        assert actual == expected
