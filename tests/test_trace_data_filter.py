import pathlib
import pandas as pd
import constants
from tracing import TraceDataCategory

from abc import ABC

from tracing.trace_data_filter import DropDuplicatesFilter, ReplaceSubTypesFilter


class BaseClass(ABC):
    pass


class SubClass1(BaseClass):
    pass


class SubClass11(SubClass1):
    pass


class SubClass2(BaseClass):
    pass


class SubClass3(BaseClass):
    pass


def get_sample_trace_data() -> pd.DataFrame:
    trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass3,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass11,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]

    trace_data = trace_data.astype(constants.TraceData.SCHEMA)
    return trace_data


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass3,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass11,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object = DropDuplicatesFilter()

    trace_data = get_sample_trace_data()
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_if_common_base_type_in_data_processes_and_returns_correct_data_and_difference():
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass3,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    test_object = ReplaceSubTypesFilter(True)
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        BaseClass,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        BaseClass,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        BaseClass,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]

    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    test_object = ReplaceSubTypesFilter(False)
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)
