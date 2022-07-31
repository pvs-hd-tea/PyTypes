import pathlib
import pandas as pd
import constants
from tracing import TraceDataCategory

from abc import ABC

from typegen.unification import DropDuplicatesFilter, ReplaceSubTypesFilter, DropVariablesOfMultipleTypesFilter, \
    TraceDataFilterList, DropTestFunctionDataFilter


class BaseClass(ABC):
    pass


class SubClass1(BaseClass):
    pass


class SubClass11(SubClass1):
    pass


class SubClass2(BaseClass):
    pass


class SubClass3(BaseClass):
    pass


def get_sample_trace_data() -> pd.DataFrame:
    trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass2,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "argument1",
        SubClass3,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass11,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        SubClass1,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        3,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        SubClass1,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "function_name",
        3,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        SubClass1,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        SubClass1,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        SubClass1,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        SubClass11,
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(pathlib.Path("tests", "filename.py")),
        BaseClass,
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        SubClass1,
    ]
    trace_data = trace_data.astype(constants.TraceData.SCHEMA)
    return trace_data


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data = expected_trace_data.drop(index=[0, 5, 7]).reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object = DropDuplicatesFilter()

    trace_data = get_sample_trace_data()
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_if_common_base_type_in_data_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data.loc[3, constants.TraceData.VARTYPENAME] = SubClass1
    expected_trace_data.loc[9, constants.TraceData.VARTYPENAME] = SubClass1
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    test_object = ReplaceSubTypesFilter(True)
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data.loc[:3, constants.TraceData.VARTYPENAME] = BaseClass
    expected_trace_data.loc[3:, constants.TraceData.VARTYPENAME] = SubClass1
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    test_object = ReplaceSubTypesFilter(False)
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_drop_variables_of_multiple_types_filter_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().iloc[[5, 6, 10]].reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    test_object = DropVariablesOfMultipleTypesFilter()
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_drop_test_function_data_filter_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().iloc[:-1].reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    test_object = DropTestFunctionDataFilter(constants.PYTEST_FUNCTION_PATTERN)

    trace_data = get_sample_trace_data()
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)


def test_trace_data_filter_list_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().iloc[[4, 5, 7]].reset_index(drop=True)
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    drop_test_function_data_filter = DropTestFunctionDataFilter(constants.PYTEST_FUNCTION_PATTERN)
    drop_duplicates_filter = DropDuplicatesFilter()
    replace_subtypes_filter = ReplaceSubTypesFilter(True)
    drop_variables_of_multiple_types_filter = DropVariablesOfMultipleTypesFilter()

    test_object = TraceDataFilterList()
    test_object.append(drop_test_function_data_filter)
    test_object.append(drop_duplicates_filter)
    test_object.append(replace_subtypes_filter)
    test_object.append(drop_duplicates_filter)
    test_object.append(drop_variables_of_multiple_types_filter)

    trace_data = get_sample_trace_data()
    actual_trace_data = test_object.get_processed_data(trace_data)

    assert expected_trace_data.equals(actual_trace_data)