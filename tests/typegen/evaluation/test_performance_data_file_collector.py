import pathlib
import numpy as np
import constants
from typegen.evaluation import PerformanceDataFileCollector


cwd = pathlib.Path.cwd() / "tests" / "resource" / "external" / "PyTypes_BinaryFiles" / "sample_performance_data_files"

sample1 = np.array([0.015, 0.23, 0.09702, 0.182])
sample2 = np.array([-0.00103, -1.9701, 2.4912, 4.7])
sample3 = np.array([2.733, 3.007, 2.6103, -9.87])


def generate_sample_files():
    np.save(cwd / ("sample1" + constants.NP_ARRAY_FILE_ENDING), sample1)
    np.save(cwd / ("sample2" + constants.NP_ARRAY_FILE_ENDING), sample2)
    np.save(cwd / "subfolder" / ("sample3" + constants.NP_ARRAY_FILE_ENDING), sample3)


def test_if_test_object_collects_generated_trace_data_in_folder_and_subfolders_and_keeps_files_it_returns_correct_performance_data():
    expected_data = np.array([sample1, sample2, sample3])

    test_object = PerformanceDataFileCollector()
    test_object.collect_data(cwd, True)
    actual_trace_data = test_object.performance_data

    assert (expected_data == actual_trace_data).all()


def test_if_test_object_collects_generated_trace_data_in_folder_it_returns_correct_performance_data():
    expected_data = np.array([sample1, sample2])

    test_object = PerformanceDataFileCollector()
    test_object.collect_data(cwd, False)
    actual_trace_data = test_object.performance_data

    assert (expected_data == actual_trace_data).all()
