import logging
from tracing.trace_data_category import TraceDataCategory

from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.drop_test_func import DropTestFunctionDataFilter

from .data import get_sample_trace_data

import constants

drop_test_filter = TraceDataFilter(  # type: ignore
    ident=DropTestFunctionDataFilter.ident, test_func_name_pattern="test_"
)


def test_factory():
    assert isinstance(drop_test_filter, DropTestFunctionDataFilter)


def test_drop_test_function_data_filter_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().iloc[:-1].reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()

    # Add test function calls in here
    trace_data.loc[len(trace_data.index)] = [
        "tests.test_file.py",
        None,
        None,
        "test_something",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        None,
        None,
        "None",
    ]

    trace_data = trace_data.astype(constants.TraceData.SCHEMA)

    actual_trace_data = drop_test_filter.apply(trace_data).astype(
        constants.TraceData.SCHEMA
    )
    logging.debug(f"{expected_trace_data.compare(actual_trace_data)}")

    assert expected_trace_data.equals(
        actual_trace_data
    ), f"{expected_trace_data.compare(actual_trace_data)}"
