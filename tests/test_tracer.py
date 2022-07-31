import os
import sys, pathlib
import pandas as pd
from typing import List, Union
import pytest
import constants
from tracing import Tracer, TraceDataCategory


def _compare_dataframes(expected: pd.DataFrame, actual: pd.DataFrame):
    if not expected.equals(actual):
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(f"expected:\n{expected}\n\n")
            print(f"actual:\n{actual}\n\n")
            print(f"diff:\n{expected.compare(actual)}")
            assert False


def sample_compare_two_int_lists(list1: List[int], list2: List[int]):
    if len(list1) != len(list2):
        return False

    for i, element1 in enumerate(list1):
        element2 = list2[i]
        are_elements_equal = sample_compare_integers(element1, element2)
        if not are_elements_equal:
            return False
    return True


def sample_compare_integers(value1: int, value2: int) -> bool:
    result = value1 == value2
    return result


def sample_get_two_variables_declared_in_one_line():
    variable1, variable2 = 1, "string"
    return variable1, variable2


def sample_convert_string_to_int(string_to_convert: str) -> Union[int, None]:
    try:
        integer = int(string_to_convert)
        return integer
    except ValueError:
        return None


class SampleClass:
    def __init__(this, integer, string):
        this.integer = integer
        this.string = string

    def sample_check_if_arguments_match_members(a, integer, string):
        are_integers_equal = a.integer == integer
        are_strings_equal = a.string == string
        return are_integers_equal and are_strings_equal


cwd = pathlib.Path.cwd()
from types import NoneType

def test_if_tracer_is_initialized_with_invalid_values_error_is_raised():
    with pytest.raises(TypeError):
        Tracer()
        Tracer(1)
        Tracer("string")


def test_if_tracer_traces_init_of_sample_class_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    integer = 5
    string = "sample"

    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    sample_class_type = SampleClass
    string_type = str
    integer_type = int
    none_type = NoneType

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "this",
        sample_class_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "integer",
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "string",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "integer",
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "string",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "__init__",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "__init__",
        none_type,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    SampleClass(integer, string)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data

    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_function_of_sample_class_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    integer = 5
    string = "sample"

    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    sample_class_type = SampleClass
    string_type = str
    integer_type = int
    bool_type = bool

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "a",
        sample_class_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "integer",
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "string",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        56,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_integers_equal",
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        57,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_strings_equal",
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "integer",
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "string",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        sample_class_type,
        "sample_check_if_arguments_match_members",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_check_if_arguments_match_members",
        bool_type,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    sample_object = SampleClass(integer, string)

    test_object.start_trace()
    sample_object.sample_check_if_arguments_match_members(integer, string)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data
    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_which_raises_error_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    invalid_string = "invalid string"
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    string_type = str
    none_type = NoneType

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_convert_string_to_int",
        41,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "string_to_convert",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_convert_string_to_int",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_convert_string_to_int",
        none_type,
    ]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_convert_string_to_int(invalid_string)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data
    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    value1 = 18
    value2 = 17
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    itype = int
    btype = bool

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value1",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value2",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        33,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        btype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_integers",
        btype,
    ]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_compare_integers(value1, value2)
    test_object.stop_trace()
    actual_trace_data = test_object.trace_data

    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_which_defines_multiple_variables_in_one_line_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    int_type = int
    string_type = str
    tuple_type = tuple

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_get_two_variables_declared_in_one_line",
        38,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable1",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_get_two_variables_declared_in_one_line",
        38,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable2",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_get_two_variables_declared_in_one_line",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_get_two_variables_declared_in_one_line",
        tuple_type,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_get_two_variables_declared_in_one_line()
    test_object.stop_trace()
    actual_trace_data = test_object.trace_data

    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_with_inner_function_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    list1 = [1, 2, 3, 4]
    list2 = [1, 2, 4, 4]
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    list_type = list
    int_type = int
    bool_type = bool

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        19,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "list1",
        list_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        19,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "list2",
        list_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        24,
        TraceDataCategory.LOCAL_VARIABLE,
        "i",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        24,
        TraceDataCategory.LOCAL_VARIABLE,
        "element1",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        25,
        TraceDataCategory.LOCAL_VARIABLE,
        "element2",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value1",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value2",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        33,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_integers",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_integers",
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        26,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_elements_equal",
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "test_tracer.py")),
        None,
        "sample_compare_two_int_lists",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_two_int_lists",
        bool_type,
    ]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_compare_two_int_lists(list1, list2)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data
    _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_starts_trace_data_is_none_or_empty():
    test_object = Tracer(cwd)

    test_object.start_trace()

    tracing_data = test_object.trace_data

    # Clears trace setup.
    test_object.stop_trace()

    assert tracing_data is None or len(tracing_data) == 0


def test_if_tracer_stops_no_trace_is_set():
    test_object = Tracer(cwd)

    test_object.stop_trace()

    assert sys.gettrace() is None
