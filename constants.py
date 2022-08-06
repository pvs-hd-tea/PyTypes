import re
import pandas as pd

PROJECT_NAME = "PyTypes"

CONFIG_FILE_NAME = "pytypes.toml"

TRACER_ATTRIBUTE = "pytype_tracer"

SAMPLE_CODE_FOLDER_NAME = "examples"

TRACE_DATA_FILE_ENDING = ".pytype"

PYTEST_FUNCTION_PATTERN = re.compile(r"test_")


class TraceData:
    FILENAME = "Filename"
    CLASS_MODULE = "Class Module"
    CLASS = "Class"
    FUNCNAME = "Function Name"
    LINENO = "Line Number"
    CATEGORY = "Category"
    VARNAME = "Name"
    VARTYPE_MODULE = "Type Module"
    VARTYPE = "Type"

    SCHEMA = {
        FILENAME: pd.StringDtype(),
        CLASS_MODULE: pd.StringDtype(),
        CLASS: pd.StringDtype(),
        FUNCNAME: pd.StringDtype(),
        LINENO: pd.UInt64Dtype(),
        CATEGORY: pd.Int64Dtype(),
        VARNAME: pd.StringDtype(),
        VARTYPE_MODULE: pd.StringDtype(),
        VARTYPE: pd.StringDtype(),
    }
