import pandas as pd
import constants
from tracing import TraceDataCategory
from typegen.evaluation import MetricDataCalculator


def get_sample_data():
    sample_original_data = pd.DataFrame(columns=constants.TraceData.TYPE_HINT_SCHEMA.keys())
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        None,
        "sample_function_name",
        10,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        int.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        25,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        bool.__name__,
    ]
    sample_original_data.loc[len(sample_original_data.index)] = [
        "sample_original_filename",
        str.__name__,
        "sample_function_name2",
        35,
        TraceDataCategory.FUNCTION_RETURN,
        "sample_function_name2",
        float.__name__,
    ]

    sample_generated_data = pd.DataFrame(columns=constants.TraceData.TYPE_HINT_SCHEMA.keys())
    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_generated_filename",
        None,
        "sample_function_name",
        10,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        int.__name__,
    ]
    sample_generated_data.loc[len(sample_generated_data.index)] = [
        "sample_generated_filename",
        str.__name__,
        "sample_function_name2",
        25,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        object.__name__,
    ]

    return sample_original_data, sample_generated_data


def test_metric_calculator_returns_correct_data():
    expected_data = pd.DataFrame(columns=constants.TraceData.METRICS_SCHEMA)
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        None,
        TraceDataCategory.FUNCTION_PARAMETER,
        True,
        True,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        TraceDataCategory.LOCAL_VARIABLE,
        True,
        False,
    ]
    expected_data.loc[len(expected_data.index)] = [
        "sample_original_filename",
        str.__name__,
        TraceDataCategory.FUNCTION_RETURN,
        False,
        False
    ]
    expected_data = expected_data.astype(constants.TraceData.METRICS_SCHEMA)
    sample_original_data, sample_generated_data = get_sample_data()
    test_object = MetricDataCalculator()
    test_object.add_filename_mapping("sample_original_filename", "sample_generated_filename")
    actual_data = test_object.get_metric_data(sample_original_data, sample_generated_data)
    assert expected_data.equals(actual_data)
