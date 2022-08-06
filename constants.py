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
        # relative path to file of variable,
        # from project root
        FILENAME: pd.StringDtype(),
        # module of class this variable is in.
        # None if not in a class' scope
        CLASS_MODULE: pd.StringDtype(),
        # name of class this variable is in.
        # None if not in a class' scope
        CLASS: pd.StringDtype(),
        # module of function this variable is in
        # None if not in a function's scope
        FUNCNAME: pd.StringDtype(),
        # line number the variable occurs on
        LINENO: pd.UInt64Dtype(),
        # number identifying context said variable appears in
        # See TraceDataCategory for more information
        CATEGORY: pd.Int64Dtype(),
        # name of the variableor, when CATEGORY indicates a FUNCTION_RETURN,
        # it is the name of the returning function
        # never None
        VARNAME: pd.StringDtype(),
        # the module of the variable's type
        # None if it is a builtin type
        VARTYPE_MODULE: pd.StringDtype(),
        # the name of the variable's type
        # never None
        VARTYPE: pd.StringDtype(),
    }
