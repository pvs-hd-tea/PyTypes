from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.drop_test_func import DropTestFunctionDataFilter

from .data import sample_trace_data

from constants import Schema

drop_test_filter = TraceDataFilter(  # type: ignore
    ident=DropTestFunctionDataFilter.ident, test_name_pat="test_"
)


def test_factory():
    assert isinstance(drop_test_filter, DropTestFunctionDataFilter)


def test_drop_test_function_data_filter_processes_and_returns_correct_data(sample_trace_data):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data = expected_trace_data.drop(index=[10, 11, 12, 13, 14]).reset_index(
        drop=True
    )
    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    trace_data = sample_trace_data.copy()
    trace_data = trace_data.astype(Schema.TraceData)
    actual_trace_data = drop_test_filter.apply(trace_data)

    assert expected_trace_data.equals(
        actual_trace_data
    ), f"{expected_trace_data.compare(actual_trace_data)}"
