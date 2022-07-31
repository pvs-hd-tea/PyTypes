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
    CLASS = "Class"
    FUNCNAME = "Function Name"
    LINENO = "Line Number"
    CATEGORY = "Category"
    VARNAME = "Name"
    VARTYPENAME = "TypeName"
    VARTYPECLASS = "TypeClass"

    SCHEMA = {
        FILENAME: pd.StringDtype(),
        CLASS: object,
        FUNCNAME: pd.StringDtype(),
        LINENO: pd.UInt64Dtype(),
        # because of TraceDataCategory's inheritance from enum.Enum
        CATEGORY: pd.StringDtype(),
        VARNAME: pd.StringDtype(),
        VARTYPENAME: pd.StringDtype(),
        VARTYPECLASS: object,
    }
