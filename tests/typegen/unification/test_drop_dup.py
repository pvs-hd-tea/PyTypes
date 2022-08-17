from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.drop_dupes import DropDuplicatesFilter

import constants

dropdup = TraceDataFilter(DropDuplicatesFilter.ident)  # type: ignore

from .data import sample_trace_data

def test_factory():
    assert isinstance(dropdup, DropDuplicatesFilter)


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference(sample_trace_data):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data = expected_trace_data.drop(index=[0, 5, 7, 11, 12, 13]).reset_index(
        drop=True
    )
    expected_trace_data = expected_trace_data.astype(constants.AnnotationData.SCHEMA)

    trace_data = sample_trace_data.copy()
    actual_trace_data = dropdup.apply(trace_data)

    assert expected_trace_data.equals(actual_trace_data)
