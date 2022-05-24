import sys, pathlib
import pandas as pd
import pytest

import constants
from tracing import Tracer, TraceDataCategory


def sample_compare(value1, value2):
    result = value1 == value2
    return result


sample_function_name = sample_compare.__name__
cwd = pathlib.Path.cwd()


def test_if_starttrace_is_called_with_invalid_arguments_typeerror_is_raised():
    with pytest.raises(TypeError):
        Tracer(cwd).start_trace()
        Tracer(cwd).start_trace(None)
        Tracer(cwd).start_trace(10)


def test_if_tracer_traces_sample_function_it_collects_correct_tracing_data():
    test_object = Tracer(cwd)
    value1 = 18
    value2 = 17
    expected_trace_data = pd.DataFrame(columns=constants.TRACE_DATA_COLUMNS)

    itype = type(5)
    btype = type(False)

    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_compare",
        9,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value1",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_compare",
        9,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "value2",
        itype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_compare",
        11,
        TraceDataCategory.LOCAL_VARIABLE,
        "result",
        btype,
    ]
    expected_trace_data.loc[len(expected_trace_data.index)] = [
        "/tests/test_tracer.py",
        "sample_compare",
        11,
        TraceDataCategory.FUNCTION_RETURN,
        None,
        btype,
    ]

    test_object.start_trace(sample_function_name)
    sample_compare(value1, value2)
    test_object.stop_trace()
    actual_trace_data = test_object.trace_data
    # Todo: Include the file name column.
    expected_trace_data = expected_trace_data.drop("Filename", axis=1)
    actual_trace_data = actual_trace_data.drop("Filename", axis=1)

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(actual_trace_data.head(n=20))
        print(expected_trace_data.head(n=20))

    assert expected_trace_data.equals(actual_trace_data)


def test_if_tracer_starts_trace_data_is_none_or_empty():
    test_object = Tracer(cwd)

    test_object.start_trace(sample_function_name)

    tracing_data = test_object.trace_data

    # Clears trace setup.
    test_object.stop_trace()

    assert tracing_data is None or len(tracing_data) == 0


def test_if_tracer_stops_no_trace_is_set():
    test_object = Tracer(cwd)

    test_object.stop_trace()

    assert sys.gettrace() is None
