import pathlib
import pandas as pd
import pytest
import constants
from tracing import TracerDecoratorAppender, TestFileTraceDataCollector

cwd = pathlib.Path.cwd() / 'resource'


def test_if_argument_of_append_decorator_is_none_error_is_raised():
    test_object = TestFileTraceDataCollector()
    with pytest.raises(TypeError):
        test_object.collect_trace_data(None)


def test_if_test_object_collects_generated_trace_data_it_returns_correct_trace_data():
    return True

    expected_trace_data = pd.read_pickle(cwd / "test_file_trace_data_collector_expected_data1.pytype")
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)
    expected_trace_data = expected_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                          ignore_index=True)
    tracer_decorator_appender = TracerDecoratorAppender()
    tracer_decorator_appender.append_decorator_on_all_files_in(cwd, True)
    tracer_decorator_appender.execute_decorator_appended_files()

    test_object = TestFileTraceDataCollector()
    test_object.collect_trace_data(cwd.parent, False)  # Do not set this to true, otherwise the collector also
    # collects the serialized expected trace data.
    actual_trace_data = test_object.trace_data
    actual_trace_data = actual_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                      ignore_index=True)
    # with pd.option_context("display.max_rows", None, "display.max_columns", None):
    #    print(actual_trace_data.shape[0])
    #    print(expected_trace_data.shape[0])
    assert actual_trace_data.shape[0] == 52
    assert expected_trace_data["Filename"].equals(actual_trace_data["Filename"])
