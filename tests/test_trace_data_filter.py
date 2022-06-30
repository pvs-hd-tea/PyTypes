import pathlib
import pandas as pd
import constants
from tracing import TraceDataCategory

from abc import ABC

from tracing.trace_data_filter import DropDuplicatesFilter


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
    subclass2_type = SubClass2
    subclass3_type = SubClass3

    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        subclass2_type,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        subclass2_type,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        subclass3_type,
    ]

    return trace_data


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    trace_data = get_sample_trace_data()

    expected_difference = 1 / float(3)
    expected_trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    subclass2_type = SubClass2
    subclass3_type = SubClass3

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        subclass2_type,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        subclass3_type,
    ]

    test_object = DropDuplicatesFilter()
    actual_trace_data, actual_difference = test_object.get_processed_data_and_difference(trace_data)
    assert abs(actual_difference - expected_difference) < 1e-8
    assert expected_trace_data.equals(actual_trace_data)
