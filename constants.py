import re
import pandas as pd

PROJECT_NAME = "PyTypes"

CONFIG_FILE_NAME = "pytypes.toml"

TRACER_ATTRIBUTE = "pytype_tracer"

TRACERS_ATTRIBUTE = "pytype_tracers"

AMOUNT_EXECUTIONS_TESTING_PERFORMANCE = 10

SAMPLE_CODE_FOLDER_NAME = "examples"

TRACE_DATA_FILE_ENDING = ".pytype"

NP_ARRAY_FILE_ENDING = ".npy_pytype"

PYTEST_FUNCTION_PATTERN = re.compile(r"test_")


class TraceData:
    FILENAME = "Filename"
    CLASS = "Class"
    FUNCNAME = "Function Name"
    LINENO = "Line Number"
    CATEGORY = "Category"
    VARNAME = "Name"
    VARTYPE = "Type"

    SCHEMA = {
        FILENAME: pd.StringDtype(),
        CLASS: object,
        FUNCNAME: pd.StringDtype(),
        LINENO: pd.UInt64Dtype(),
        # because of TraceDataCategory's inheritance from enum.Enum
        CATEGORY: pd.StringDtype(),
        VARNAME: pd.StringDtype(),
        VARTYPE: object,
    }
