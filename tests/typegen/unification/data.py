import abc
import pathlib

import pandas as pd

from constants import Schema
from common import TraceDataCategory

import pytest


class BaseClass(abc.ABC):
    pass


class SubClass1(BaseClass):
    pass


class SubClass11(SubClass1):
    pass


class SubClass2(BaseClass):
    pass


class SubClass3(BaseClass):
    pass


resource_path = pathlib.Path("tests", "typegen", "unification", "data.py")
resource_module = "tests.typegen.unification.data"


@pytest.fixture()
def sample_trace_data() -> pd.DataFrame:
    trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "argument1",
        resource_module,
        "SubClass2",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "argument1",
        resource_module,
        "SubClass2",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "argument1",
        resource_module,
        "SubClass3",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        resource_module,
        "SubClass11",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable1",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        3,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "function_name",
        3,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable2",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member1",
        resource_module,
        "SubClass11",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        resource_module,
        "SubClass1",
    ]
    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        "BaseClass",
        "test_function_name",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "local_variable",
        resource_module,
        "SubClass2",
    ]
    trace_data = trace_data.astype(Schema.TraceData)
    return trace_data
