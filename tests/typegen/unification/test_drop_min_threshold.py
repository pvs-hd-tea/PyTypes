from typegen.unification.drop_min_threshold import MinThresholdFilter
from typegen.unification.filter_base import TraceDataFilter

from .data import sample_trace_data

import constants

drop_min_threshold = TraceDataFilter(MinThresholdFilter.ident)  # type: ignore


def test_factory():
    assert isinstance(drop_min_threshold, MinThresholdFilter)


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference(
    sample_trace_data,
):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data = expected_trace_data.drop(index=14).reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.AnnotationData.SCHEMA)

    trace_data = sample_trace_data.copy()
    actual_trace_data = drop_min_threshold.apply(trace_data)

    assert expected_trace_data.equals(actual_trace_data)
