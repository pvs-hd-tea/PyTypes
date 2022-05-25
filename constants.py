import pandas as pd

# Tracing
PROJECT_NAME = "PyTypes"


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
        CATEGORY: pd.CategoricalDtype(),
        VARNAME: pd.StringDtype(),
        VARTYPE: object,
    }
