import pathlib
import pandas as pd
import constants
from typegen.evaluation import FileTypeHintsCollector

path_sample_file = pathlib.Path.cwd() / "tests" / "resource" / "typegen" / "evaluation" / "file_with_type_hints.py"
path_sample_data_file = pathlib.Path.cwd() / "tests" / "resource" / "external" / "PyTypes_BinaryFiles" / "sample_typehint_data_files"


def test_file_type_hints_collector_returns_correct_data():
    expected_trace_data_file_path = path_sample_data_file / "sample1.pytype"
    expected_typehint_data = pd.read_pickle(expected_trace_data_file_path)
    expected_typehint_data = expected_typehint_data.astype(constants.TraceData.TYPE_HINT_SCHEMA)

    test_object = FileTypeHintsCollector(pathlib.Path.cwd())
    test_object.collect_data([path_sample_file])
    actual_typehint_data = test_object.typehint_data

    print(actual_typehint_data)

    assert actual_typehint_data.shape[0] == 22
    assert expected_typehint_data.equals(actual_typehint_data)


def test_file_type_hints_collector_returns_correct_data_for_multiple_files():
    expected_trace_data_file_path = path_sample_data_file / "sample2.pytype"
    expected_typehint_data = pd.read_pickle(expected_trace_data_file_path)
    expected_typehint_data = expected_typehint_data.astype(constants.TraceData.TYPE_HINT_SCHEMA)

    test_object = FileTypeHintsCollector(pathlib.Path.cwd())
    test_object.collect_data([path_sample_file, path_sample_file])
    actual_typehint_data = test_object.typehint_data

    print(actual_typehint_data)

    assert actual_typehint_data.shape[0] == 44
    assert expected_typehint_data.equals(actual_typehint_data)
