import sys, pathlib
import pandas as pd
import pytest
from typing import List, Union
import constants
from tracing import Tracer, TraceDataCategory


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


cwd = pathlib.Path.cwd().parent


def test_if_tracer_traces_sample_function_which_raises_error_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    invalid_string = "invalid string"
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    string_type = type(invalid_string)
    none_type = type(None)

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_convert_string_to_int",
        31,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "string_to_convert",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_convert_string_to_int",
        36,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_convert_string_to_int",
        none_type,
    ]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_convert_string_to_int(invalid_string)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data

    # Todo: Include the file name column.
    expected_trace_data = expected_trace_data.drop("Filename", axis=1)
    actual_trace_data = actual_trace_data.drop("Filename", axis=1)

    assert expected_trace_data.equals(actual_trace_data)


def test_if_tracer_traces_sample_function_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    value1 = 18
    value2 = 17
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    itype = type(5)
    btype = type(False)

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "tests/test_tracer.py",
        "sample_compare_integers",
        21,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value1",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "tests/test_tracer.py",
        "sample_compare_integers",
        21,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value2",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "tests/test_tracer.py",
        "sample_compare_integers",
        23,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        btype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "tests/test_tracer.py",
        "sample_compare_integers",
        23,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_integers",
        btype,
    ]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_compare_integers(value1, value2)
    test_object.stop_trace()
    actual_trace_data = test_object.trace_data

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(actual_trace_data.head(n=20))

    assert expected_trace_data.equals(actual_trace_data)


def test_if_tracer_traces_sample_function_which_defines_multiple_variables_in_one_line_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    int_type = type(1)
    string_type = type("string")
    tuple_type = type((int_type, string_type))

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_get_two_variables_declared_in_one_line",
        28,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable1",
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_get_two_variables_declared_in_one_line",
        28,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable2",
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_get_two_variables_declared_in_one_line",
        28,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_get_two_variables_declared_in_one_line",
        tuple_type,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_get_two_variables_declared_in_one_line()
    test_object.stop_trace()
    actual_trace_data = test_object.trace_data

    # Todo: Include the file name column.
    expected_trace_data = expected_trace_data.drop("Filename", axis=1)
    actual_trace_data = actual_trace_data.drop("Filename", axis=1)

    assert expected_trace_data.equals(actual_trace_data)


def test_if_tracer_traces_sample_function_with_inner_function_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    list1 = [1, 2, 3, 4]
    list2 = [1, 2, 4, 4]
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    list_type = type(list1)
    int_type = type(1)
    bool_type = type(True)

    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists', 9,
                                                               TraceDataCategory.FUNCTION_ARGUMENT, 'list1', list_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists', 9,
                                                               TraceDataCategory.FUNCTION_ARGUMENT,
                                                               'list2', list_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists',
                                                               14,
                                                               TraceDataCategory.LOCAL_VARIABLE,
                                                               'i', int_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists',
                                                               14,
                                                               TraceDataCategory.LOCAL_VARIABLE,
                                                               'element1', int_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists', 15,
                                                               TraceDataCategory.LOCAL_VARIABLE,
                                                               'element2', int_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_integers', 21,
                                                               TraceDataCategory.FUNCTION_ARGUMENT,
                                                               'value1', int_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_integers',
                                                               21,
                                                               TraceDataCategory.FUNCTION_ARGUMENT,
                                                               'value2', int_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_integers',
                                                               23,
                                                               TraceDataCategory.LOCAL_VARIABLE,
                                                               'result', bool_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_integers',
                                                               23,
                                                               TraceDataCategory.FUNCTION_RETURN,
                                                               'sample_compare_integers', bool_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists',
                                                               16,
                                                               TraceDataCategory.LOCAL_VARIABLE,
                                                               'are_elements_equal', bool_type]
    expected_trace_data.loc[len(expected_trace_data.index)] = ['/tests/test_tracer.py', 'sample_compare_two_int_lists',
                                                               17,
                                                               TraceDataCategory.FUNCTION_RETURN,
                                                               'sample_compare_two_int_lists', bool_type]
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object.start_trace()
    sample_compare_two_int_lists(list1, list2)
    test_object.stop_trace()

    actual_trace_data = test_object.trace_data
    # Todo: Include the file name column.
    expected_trace_data = expected_trace_data.drop('Filename', axis=1)
    actual_trace_data = actual_trace_data.drop('Filename', axis=1)
    #with pd.option_context("display.max_rows", None, "display.max_columns", None):
    #    print(actual_trace_data.head(n=20))
    #    print(actual_trace_data.dtypes)
    #    print(expected_trace_data.dtypes)
    assert expected_trace_data.equals(actual_trace_data)


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
