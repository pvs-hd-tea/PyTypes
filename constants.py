import pandas as pd

PROJECT_NAME = "PyTypes"

CONFIG_FILE_NAME = "pytypes.toml"

TRACER_ATTRIBUTE = "pytype_tracer"


class TraceData:
    FILENAME = "Filename"
    FUNCNAME = "Function Name"
    LINENO = "Line Number"
    CATEGORY = "Category"
    VARNAME = "Name"
    VARTYPE = "Type"

    SCHEMA = {
        FILENAME: pd.StringDtype(),
        FUNCNAME: pd.StringDtype(),
        LINENO: pd.UInt64Dtype(),
        # because of TraceDataCategory's inheritance from enum.Enum
        CATEGORY: pd.StringDtype(),
        VARNAME: pd.StringDtype(),
        VARTYPE: object,
    }
