import pathlib
import pandas as pd
import constants
from typegen import TraceDataFileCollector

cwd = pathlib.Path.cwd() / "tests" / "resource" / "external" / "PyTypes_BinaryFiles" / "sample_trace_data_files"


def test_if_test_object_collects_generated_trace_data_in_folder_and_subfolders_and_keeps_files_it_returns_correct_trace_data():
    expected_trace_data_file_path = cwd / "samples_rglob.test_pytype"
    expected_trace_data = pd.read_pickle(expected_trace_data_file_path)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object = TraceDataFileCollector()
    test_object.collect_data(cwd, True)
    actual_trace_data = test_object.trace_data

    # with pd.option_context("display.max_rows", None, "display.max_columns", None):
    #   print(actual_trace_data.shape[0])
    #   print(expected_trace_data.shape[0])

    assert actual_trace_data.shape[0] == 20
    assert expected_trace_data.equals(actual_trace_data)


def test_if_test_object_collects_generated_trace_data_in_folder_it_returns_correct_trace_data():
    expected_trace_data_file_path = cwd / "samples_glob.test_pytype"
    expected_trace_data = pd.read_pickle(expected_trace_data_file_path)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object = TraceDataFileCollector()
    test_object.collect_data(cwd, False)
    actual_trace_data = test_object.trace_data

    assert actual_trace_data.shape[0] == 14
    assert expected_trace_data.equals(actual_trace_data)
