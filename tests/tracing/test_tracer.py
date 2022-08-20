import os
import sys
import pathlib
import pandas as pd
from typing import List, Union
from tracing import Tracer, TraceDataCategory
from constants import Column, Schema


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


def create_and_set_global():
    global a_global_var
    a_global_var = "Interesting Data"
    return None


def modify_global():
    global a_global_var
    a_global_var = 42
    return None


def read_from_global() -> str:
    global a_global_var
    return a_global_var


cwd = pathlib.Path.cwd()
from types import NoneType

proj_path = pathlib.Path.cwd()
venv_path = pathlib.Path(os.environ["VIRTUAL_ENV"])
import pathlib

stdlib_path = pathlib.Path(pathlib.__file__).parent

import pytest


@pytest.fixture(scope="function")
def tracers() -> tuple[Tracer, Tracer]:
    opt = Tracer(
        proj_path=proj_path,
        venv_path=venv_path,
        stdlib_path=stdlib_path,
        apply_opts=True,
    )
    nonopt = Tracer(
        proj_path=proj_path,
        venv_path=venv_path,
        stdlib_path=stdlib_path,
        apply_opts=False,
    )

    return opt, nonopt


def test_if_tracer_traces_init_of_sample_class_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    integer = 5
    string = "sample"

    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    sample_class_module = "tests.tracing.test_tracer"
    sample_class_type = "SampleClass"
    string_type = "str"
    integer_type = "int"
    none_type = "NoneType"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_PARAMETER,
        "this",
        sample_class_module,
        sample_class_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_PARAMETER,
        "integer",
        None,
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        "__init__",
        50,
        TraceDataCategory.FUNCTION_PARAMETER,
        "string",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "integer",
        None,
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "string",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        sample_class_module,
        sample_class_type,
        "__init__",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "__init__",
        None,
        none_type,
    ]

    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    for tracer in tracers:
        tracer.start_trace()
        SampleClass(integer, string)
        tracer.stop_trace()

        actual_trace_data = tracer.trace_data

        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_function_of_sample_class_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    integer = 5
    string = "sample"

    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    module = "tests.tracing.test_tracer"

    sample_class_type = "SampleClass"
    string_type = "str"
    integer_type = "int"
    bool_type = "bool"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        module,
        sample_class_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_PARAMETER,
        "integer",
        None,
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        54,
        TraceDataCategory.FUNCTION_PARAMETER,
        "string",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        55,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_integers_equal",
        None,
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        56,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_strings_equal",
        None,
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "integer",
        None,
        integer_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "string",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        module,
        sample_class_type,
        "sample_check_if_arguments_match_members",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_check_if_arguments_match_members",
        None,
        bool_type,
    ]

    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    sample_object = SampleClass(integer, string)

    for tracer in tracers:
        tracer.start_trace()
        sample_object.sample_check_if_arguments_match_members(integer, string)
        tracer.stop_trace()

        actual_trace_data = tracer.trace_data
        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_which_raises_error_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    invalid_string = "invalid string"
    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    string_type = "str"
    none_type = "NoneType"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_convert_string_to_int",
        41,
        TraceDataCategory.FUNCTION_PARAMETER,
        "string_to_convert",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_convert_string_to_int",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_convert_string_to_int",
        None,
        none_type,
    ]
    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    for tracer in tracers:
        tracer.start_trace()
        sample_convert_string_to_int(invalid_string)
        tracer.stop_trace()

        actual_trace_data = tracer.trace_data
        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    value1 = 18
    value2 = 17
    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    itype = "int"
    btype = "bool"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_PARAMETER,
        "value1",
        None,
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_PARAMETER,
        "value2",
        None,
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        32,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        None,
        btype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_integers",
        None,
        btype,
    ]
    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    for tracer in tracers:
        tracer.start_trace()
        sample_compare_integers(value1, value2)
        tracer.stop_trace()
        actual_trace_data = tracer.trace_data

        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_which_defines_multiple_variables_in_one_line_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    int_type = "int"
    string_type = "str"
    tuple_type = "tuple"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_get_two_variables_declared_in_one_line",
        37,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable1",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_get_two_variables_declared_in_one_line",
        37,
        TraceDataCategory.LOCAL_VARIABLE,
        "variable2",
        None,
        string_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_get_two_variables_declared_in_one_line",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_get_two_variables_declared_in_one_line",
        None,
        tuple_type,
    ]

    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    for tracer in tracers:
        tracer.start_trace()
        sample_get_two_variables_declared_in_one_line()
        tracer.stop_trace()
        actual_trace_data = tracer.trace_data

        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_traces_sample_function_with_inner_function_it_collects_correct_tracing_data(
    tracers: list[Tracer],
):
    list1 = [1, 2, 3, 4]
    list2 = [1, 2, 4, 4]
    expected_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    list_type = "list"
    int_type = "int"
    bool_type = "bool"

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        19,
        TraceDataCategory.FUNCTION_PARAMETER,
        "list1",
        None,
        list_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        19,
        TraceDataCategory.FUNCTION_PARAMETER,
        "list2",
        None,
        list_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        23,
        TraceDataCategory.LOCAL_VARIABLE,
        "i",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        23,
        TraceDataCategory.LOCAL_VARIABLE,
        "element1",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        24,
        TraceDataCategory.LOCAL_VARIABLE,
        "element2",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_PARAMETER,
        "value1",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        31,
        TraceDataCategory.FUNCTION_PARAMETER,
        "value2",
        None,
        int_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        32,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        None,
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_integers",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_integers",
        None,
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        25,
        TraceDataCategory.LOCAL_VARIABLE,
        "are_elements_equal",
        None,
        bool_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "tracing", "test_tracer.py")),
        None,
        None,
        "sample_compare_two_int_lists",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_compare_two_int_lists",
        None,
        bool_type,
    ]
    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    for tracer in tracers:
        tracer.start_trace()
        sample_compare_two_int_lists(list1, list2)
        tracer.stop_trace()

        actual_trace_data = tracer.trace_data
        _compare_dataframes(expected_trace_data, actual_trace_data)


def test_if_tracer_starts_trace_data_is_none_or_empty(tracers: list[Tracer]):
    for tracer in tracers:
        tracer.start_trace()

        tracing_data = tracer.trace_data

        # Clears trace setup.
        tracer.stop_trace()

        assert tracing_data is None or len(tracing_data) == 0


def test_if_tracer_stops_no_trace_is_set(tracers: list[Tracer]):
    for tracer in tracers:
        tracer.stop_trace()
        assert sys.gettrace() is None


import logging


def test_tracer_finds_globals(tracers: list[Tracer]):
    expected = pd.DataFrame(columns=Schema.TraceData.keys())

    filepath = str(pathlib.Path("tests", "tracing", "test_tracer.py"))

    expected.loc[len(expected.index)] = [
        filepath,
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "a_global_var",
        None,
        int.__name__,
    ]
    expected.loc[len(expected.index)] = [
        filepath,
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "a_global_var",
        None,
        str.__name__,
    ]

    for tracer in tracers:
        with tracer.active_trace():
            create_and_set_global()
            _ = read_from_global()
            modify_global()
            _ = read_from_global()

        trace_data = tracer.trace_data
        logging.debug(f"\n{trace_data}")

        subset = expected.merge(trace_data, how="inner")
        assert len(subset) == len(expected), f"Did not find all globals!\n{trace_data}"

