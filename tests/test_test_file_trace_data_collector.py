import pathlib
import pandas as pd
import pytest
import constants
from tracing import TestFileTraceDataCollector

cwd = pathlib.Path.cwd() / 'resource'


def delete_trace_data_files_in_tests():
    """ Deletes all trace data files in tests. """
    trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    trace_data = trace_data.astype(constants.TraceData.SCHEMA)

    file_ending = constants.TRACE_DATA_FILE_ENDING
    file_pattern = "*" + file_ending

    potential_trace_data_file_paths = cwd.parent.rglob(file_pattern)

    for potential_trace_data_file_path in potential_trace_data_file_paths:
        potential_trace_data = pd.read_pickle(potential_trace_data_file_path)
        if (trace_data.dtypes == potential_trace_data.dtypes).all():
            potential_trace_data_file_path.unlink()


def test_if_test_object_collects_generated_trace_data_and_keeps_files_it_returns_correct_trace_data_and_files_are_kept():
    # Todo: Make the tests work in the CI pipeline.
    return

    delete_trace_data_files_in_tests()

    expected_trace_data_file_path = [path for path in cwd.rglob("test_file_trace_data_collector_expected_data1.test_pytype")][0]
    expected_trace_data = pd.read_pickle(expected_trace_data_file_path)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)
    expected_trace_data = expected_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                          ignore_index=True)
    tracer_decorator_appender = TracerDecoratorAppender()
    tracer_decorator_appender.append_decorator_on_all_files_in(cwd, True)
    tracer_decorator_appender.execute_decorator_appended_files()

    test_object = TestFileTraceDataCollector()
    test_object.collect_trace_data(cwd.parent, True, False)
    actual_trace_data = test_object.trace_data
    actual_trace_data = actual_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                      ignore_index=True)
    # with pd.option_context("display.max_rows", None, "display.max_columns", None):
    #    print(actual_trace_data.shape[0])
    #    print(expected_trace_data.shape[0])

    assert actual_trace_data.shape[0] == 52
    assert expected_trace_data["Filename"].equals(actual_trace_data["Filename"])

    pytype_trace_data_files = [path for path in cwd.parent.rglob("*" + constants.TRACE_DATA_FILE_ENDING)]
    assert len(pytype_trace_data_files) == 6
    delete_trace_data_files_in_tests()


def test_if_test_object_collects_generated_trace_data_and_deletes_files_it_returns_correct_trace_data_and_files_are_deleted():
    # Todo: Make the tests work in the CI pipeline.
    return

    delete_trace_data_files_in_tests()

    expected_trace_data_file_path = [path for path in cwd.rglob("test_file_trace_data_collector_expected_data1.test_pytype")][0]
    expected_trace_data = pd.read_pickle(expected_trace_data_file_path)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)
    expected_trace_data = expected_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                          ignore_index=True)
    tracer_decorator_appender = TracerDecoratorAppender()
    tracer_decorator_appender.append_decorator_on_all_files_in(cwd, True)
    tracer_decorator_appender.execute_decorator_appended_files()

    test_object = TestFileTraceDataCollector()
    test_object.collect_trace_data(cwd.parent, True, True)
    actual_trace_data = test_object.trace_data
    actual_trace_data = actual_trace_data.sort_values(by=['Filename', 'Function Name', 'Line Number'],
                                                      ignore_index=True)
    # with pd.option_context("display.max_rows", None, "display.max_columns", None):
    #    print(actual_trace_data.shape[0])
    #    print(expected_trace_data.shape[0])

    assert actual_trace_data.shape[0] == 52
    assert expected_trace_data["Filename"].equals(actual_trace_data["Filename"])

    pytype_trace_data_files = [path for path in cwd.parent.rglob("*" + constants.TRACE_DATA_FILE_ENDING)]
    assert len(pytype_trace_data_files) == 0

    delete_trace_data_files_in_tests()
