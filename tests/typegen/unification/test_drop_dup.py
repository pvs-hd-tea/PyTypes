from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.drop_dupes import DropDuplicatesFilter

from .data import get_sample_trace_data

import constants

dropdup = TraceDataFilter(DropDuplicatesFilter.ident)

def test_factory():
    assert isinstance(dropdup, DropDuplicatesFilter)

def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data = expected_trace_data.drop(index=[0, 5, 7]).reset_index(
        drop=True
    )
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    actual_trace_data = dropdup.apply(trace_data)

    assert expected_trace_data.equals(actual_trace_data)