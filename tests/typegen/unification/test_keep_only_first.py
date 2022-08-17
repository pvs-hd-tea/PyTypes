from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.keep_only_first import KeepOnlyFirstFilter

from .data import sample_trace_data

from constants import Schema, Column

keep_only_first = TraceDataFilter(KeepOnlyFirstFilter.ident)  # type: ignore


def test_factory():
    assert isinstance(keep_only_first, KeepOnlyFirstFilter)


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference(sample_trace_data):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data = expected_trace_data.iloc[[0, 3, 5, 7, 10]].reset_index(
        drop=True
    )
    expected_trace_data = expected_trace_data.astype(Schema.TraceData)

    trace_data = sample_trace_data.copy()
    actual_trace_data = keep_only_first.apply(trace_data)

    assert expected_trace_data.equals(actual_trace_data)
