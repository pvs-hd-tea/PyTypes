def normalize_type(type_hint: str) -> str:
    """Gets the type union written as a type union using only | .
    Normalizes typing.Union, typing.Optional and | unions.
    Does also normalize inner type unions, for example: list[int | str]."""
    types = _normalize_type(type_hint)

    returned_type = ""
    sorted_union_types = sorted(set(types))
    for i, type_name in enumerate(sorted_union_types):
        if i == 0:
            returned_type = type_name
        else:
            returned_type += " | " + type_name
    return returned_type


def _normalize_type(type_hint: str) -> list[str]:
    types_in_union = _normalize_union(type_hint)
    if len(types_in_union) == 1:
        types = _normalize_type_with_inner_types(type_hint)
    else:
        types = types_in_union
    return types


def _normalize_union(union_type_hint: str) -> list[str]:
    returned_types = []
    union_type_hint_without_spaces = union_type_hint.replace(" ", "")
    types_in_union = _get_split_outside_of_brackets(union_type_hint_without_spaces, "|")
    is_union_using_vertical_bar = len(types_in_union) > 1
    is_union = (
        union_type_hint_without_spaces.startswith("typing.Union[")
        or union_type_hint_without_spaces.startswith("Union[")
    ) and union_type_hint_without_spaces.endswith("]")
    is_optional = (
        union_type_hint_without_spaces.startswith("typing.Optional[")
        or union_type_hint_without_spaces.startswith("Optional[")
    ) and union_type_hint_without_spaces.endswith("]")
    if not is_union_using_vertical_bar and not is_union and not is_optional:
        return [union_type_hint]

    if not is_union_using_vertical_bar:
        union_within_left_bracket = union_type_hint_without_spaces.split("[", 1)[1]
        content_within_brackets = union_within_left_bracket.rsplit("]", 1)[0]
        types_in_union = _get_split_outside_of_brackets(content_within_brackets, ",")
        if is_optional:
            types_in_union.append("None")

    for type_in_union in types_in_union:
        if type_in_union.replace(" ", "") == union_type_hint_without_spaces:
            raise ValueError(f"Infinite recursion detected for {union_type_hint}!")
        returned_types += _normalize_type(type_in_union)
    return returned_types


def _normalize_type_with_inner_types(type_with_inner_types_hint: str) -> list[str]:
    type_with_inner_types_hint_without_spaces = type_with_inner_types_hint.replace(
        " ", ""
    )
    is_invalid_type_with_inner_types = (
        type_with_inner_types_hint_without_spaces.startswith("typing.Union[")
        or type_with_inner_types_hint_without_spaces.startswith("Union[")
        or type_with_inner_types_hint_without_spaces.startswith("typing.Optional[")
        or type_with_inner_types_hint_without_spaces.startswith("Optional[")
    )
    if is_invalid_type_with_inner_types:
        raise ValueError(type_with_inner_types_hint_without_spaces)

    if not _is_type_with_inner_types(type_with_inner_types_hint_without_spaces):
        return [type_with_inner_types_hint]

    split_elements = type_with_inner_types_hint_without_spaces.split("[", 1)
    outer_type = split_elements[0]
    inner_content = split_elements[1][:-1]
    inner_types = _get_split_outside_of_brackets(inner_content, ",")
    normalized_type = outer_type + "["
    inner_content = ""
    for i, inner_type in enumerate(inner_types):
        normalized_inner_type = normalize_type(inner_type)
        if i == 0:
            inner_content = normalized_inner_type
        else:
            inner_content += ", " + normalized_inner_type
    normalized_type += inner_content + "]"
    return [normalized_type]


def _is_type_with_inner_types(type_hint: str) -> bool:
    bracket_depth = 0
    opening_bracket_letter = "["
    closing_bracket_letter = "]"

    for i, char in enumerate(type_hint):
        if char == opening_bracket_letter:
            bracket_depth += 1

        if char == closing_bracket_letter:
            bracket_depth -= 1
            if bracket_depth < 0:
                raise ValueError(type_hint)
            elif bracket_depth == 0:
                if i == len(type_hint) - 1:
                    return True
                else:
                    return False
    return False


def _get_split_outside_of_brackets(type_hint: str, letter_to_split) -> list[str]:
    bracket_depth = 0
    opening_bracket_letter = "["
    closing_bracket_letter = "]"

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
                    raise ValueError(
                        f"{type_hint} does not have correctly set brackets!"
                    )
            current_split_element += char
    split_elements.append(current_split_element)
    return split_elements
