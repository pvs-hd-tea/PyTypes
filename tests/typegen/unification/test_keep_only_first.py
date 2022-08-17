from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.keep_only_first import KeepOnlyFirstFilter

from .data import get_sample_trace_data

import constants

keep_only_first = TraceDataFilter(KeepOnlyFirstFilter.ident)  # type: ignore


def test_factory():
    assert isinstance(keep_only_first, KeepOnlyFirstFilter)


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data = expected_trace_data.iloc[[0, 3, 5, 7, 10]].reset_index(
        drop=True
    )
    expected_trace_data = expected_trace_data.astype(constants.AnnotationData.SCHEMA)

    trace_data = get_sample_trace_data()
    actual_trace_data = keep_only_first.apply(trace_data)

    assert expected_trace_data.equals(actual_trace_data)
