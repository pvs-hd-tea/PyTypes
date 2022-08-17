import pandas as pd
import constants
from tracing import TraceDataCategory
from typegen.evaluation import MetricDataCalculator

from constants import Schema

def get_sample_data():
    sample_original_data = pd.DataFrame(columns=Schema.TypeHintData.keys())
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        None,
        "sample_function_name",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        int.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        bool.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        12,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        int.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        str.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_function_name2",
        float.__name__,
    ]

    sample_generated_data = pd.DataFrame(columns=Schema.TypeHintData.keys())
    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_generated_filename",
        None,
        "sample_function_name",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        int.__name__,
    ]
    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        str.__name__,
    ]

    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        str.__name__,
    ]

    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_generated_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        str.__name__,
    ]

    return sample_original_data, sample_generated_data


def test_metric_calculator_returns_correct_metric_data():
    expected_data = pd.DataFrame(columns=Schema.Metrics)
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        None,
        "sample_function_name",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        int.__name__,
        int.__name__,
        True,
        True,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        bool.__name__,
        str.__name__,
        True,
        False,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        12,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        int.__name__,
        None,
        False,
        False,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        str.__name__,
        str.__name__,
        True,
        True,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_function_name2",
        float.__name__,
        None,
        False,
        False
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        None,
        str.__name__,
        None,
        None,
    ]

    expected_data = expected_data.astype(Schema.Metrics)
    sample_original_data, sample_generated_data = get_sample_data()
    test_object = MetricDataCalculator()
    test_object.add_filename_mapping("sample_original_filename", "sample_generated_filename")
    actual_data = test_object.get_metric_data(sample_original_data, sample_generated_data)

    print(actual_data)

    assert expected_data.equals(actual_data)


def test_metric_calculator_returns_correct_completeness_and_correctness():
    expected_completeness = 3 / 5
    expected_correctness = 2 / 3
    sample_original_data, sample_generated_data = get_sample_data()

    test_object = MetricDataCalculator()
    test_object.add_filename_mapping("sample_original_filename", "sample_generated_filename")
    metric_data = test_object.get_metric_data(sample_original_data, sample_generated_data)
    total_completeness, total_correctness = test_object.get_total_completeness_and_correctness(metric_data)

    assert abs(total_completeness - expected_completeness) < 1e-8
    assert abs(total_correctness - expected_correctness) < 1e-8
