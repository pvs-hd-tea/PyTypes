import sys
import pytest
from tracing import Tracer, TraceDataElement, TraceDataCategory


def sample_compare(value1, value2):
    result = value1 == value2
    return result


sample_function_name = sample_compare.__name__


def test_if_starttrace_is_called_with_invalid_arguments_typeerror_is_raised():
    with pytest.raises(TypeError):
        Tracer().starttrace()
        Tracer().starttrace(None)
        Tracer().starttrace(10)


def test_if_tracer_traces_sample_function_it_collects_correct_tracing_data():
    test_object = Tracer()
    value1 = 18
    value2 = 17
    expected_trace_data = [
        TraceDataElement('\\tests\\test_tracer.py', 'sample_compare', 6, TraceDataCategory.FUNCTION_ARGUMENT, 'value1', 'int'),
        TraceDataElement('\\tests\\test_tracer.py', 'sample_compare', 6, TraceDataCategory.FUNCTION_ARGUMENT,
                         'value2', 'int'),
        TraceDataElement('\\tests\\test_tracer.py', 'sample_compare', 7, TraceDataCategory.LOCAL_VARIABLE,
                         'result', 'bool'),
        TraceDataElement('\\tests\\test_tracer.py', 'sample_compare', 8, TraceDataCategory.FUNCTION_RETURN,
                         None, 'bool')
    ]

    test_object.starttrace(sample_function_name)
    sample_compare(value1, value2)
    test_object.stoptrace()
    actual_trace_data = test_object.trace_data
    assert len(expected_trace_data) == len(actual_trace_data)
    for i in range(len(actual_trace_data)):
        expected_trace_data_element = expected_trace_data[i]
        actual_trace_data_element = actual_trace_data[i]
        assert expected_trace_data_element == actual_trace_data_element


def test_if_tracer_starts_trace_data_is_none_or_empty():
    test_object = Tracer()

    test_object.starttrace(sample_function_name)

    tracing_data = test_object.trace_data

    # Clears trace setup.
    test_object.stoptrace()

    assert tracing_data is None or len(tracing_data) == 0

def test_if_tracer_stops_no_trace_is_set():
    test_object = Tracer()

    test_object.stoptrace()

    assert sys.gettrace() is None
