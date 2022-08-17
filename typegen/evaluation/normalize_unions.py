def union_normalized(type_hint: str) -> str:
    """Gets the type union written as a type union using only | .
    Normalizes typing.Union, typing.Optional and | unions.
    Does NOT normalize inner type unions, for example: list[int | str]."""
    types_in_union = _get_types_in_union(type_hint)
    if len(types_in_union) == 1:
        return types_in_union[0]

    sorted_types_without_duplicates = sorted(set(types_in_union))
    returned_type = ""
    for i, type_name in enumerate(sorted_types_without_duplicates):
        if i == 0:
            returned_type = type_name
        else:
            returned_type += " | " + type_name
    return returned_type


def _get_types_in_union(union_type_hint: str) -> list[str]:
    union_type_hint = union_type_hint.replace(' ', '')

    returned_types = []
    types_in_union = _get_split_outside_of_brackets(union_type_hint, '|')
    is_union_using_vertical_bar = len(types_in_union) > 1
    is_union = (union_type_hint.startswith("typing.Union[") or union_type_hint.startswith(
        "Union[")) and union_type_hint.endswith(']')
    is_optional = (union_type_hint.startswith("typing.Optional[") or union_type_hint.startswith(
        "Optional[")) and union_type_hint.endswith(']')
    if not is_union_using_vertical_bar and not is_union and not is_optional:
        return [union_type_hint]

    if not is_union_using_vertical_bar:
        union_within_left_bracket = union_type_hint.split('[', 1)[1]
        content_within_brackets = union_within_left_bracket.rsplit(']', 1)[0]
        types_in_union = _get_split_outside_of_brackets(content_within_brackets, ',')
        if is_optional:
            types_in_union.append("None")

    for type_in_union in types_in_union:
        if type_in_union == union_type_hint:
            raise ValueError(f"Infinite recursion detected for {union_type_hint}!")
        returned_types += _get_types_in_union(type_in_union)
    return returned_types


def _get_split_outside_of_brackets(type_hint: str, letter_to_split) -> list[str]:
    bracket_depth = 0
    opening_bracket_letter = '['
    closing_bracket_letter = ']'

    split_elements = []
    current_split_element = ""
    for char in type_hint:
        if bracket_depth == 0 and char == letter_to_split:
            split_elements.append(current_split_element)
            current_split_element = ""
        else:
            if char == opening_bracket_letter:
                bracket_depth += 1
            if char == closing_bracket_letter:
                bracket_depth -= 1
                if bracket_depth < 0:
                    raise ValueError(f"{type_hint} does not have correctly set brackets!")
            current_split_element += char
    split_elements.append(current_split_element)
    return split_elements
