import re
import pandas as pd

ORIGINAL_REPOSITORY_FOLDER_NAME = "Original"

PROJECT_NAME = "PyTypes"

CONFIG_FILE_NAME = "pytypes.toml"

TRACERS_ATTRIBUTE = "pytype_tracers"

AMOUNT_EXECUTIONS_TESTING_PERFORMANCE = 10

SAMPLE_CODE_FOLDER_NAME = "examples"

TRACE_DATA_FILE_ENDING = ".pytype"

NP_ARRAY_FILE_ENDING = ".npy_pytype"

PYTEST_FUNCTION_PATTERN = re.compile(r"test_")


class Column:
    FILENAME = "Filename"
    CLASS_MODULE = "ClassModule"
    CLASS = "Class"
    FUNCNAME = "FunctionName"
    LINENO = "LineNo"
    CATEGORY = "Category"
    VARNAME = "VarName"
    VARTYPE_MODULE = "TypeModule"
    VARTYPE = "Type"

    COLUMN_OFFSET = "ColumnOffset"
    VARTYPE_ORIGINAL = "OriginalType"
    VARTYPE_GENERATED = "GeneratedType"
    COMPLETENESS = "Completeness"
    CORRECTNESS = "Correctness"


class Schema:
    TraceData = {
        # relative path to file of variable,
        # from project root
        Column.FILENAME: pd.StringDtype(),
        # module of class this variable is in.
        # None if not in a class' scope
        Column.CLASS_MODULE: pd.StringDtype(),
        # name of class this variable is in.
        # None if not in a class' scope
        Column.CLASS: pd.StringDtype(),
        # module of function this variable is in
        # None if not in a function's scope
        Column.FUNCNAME: pd.StringDtype(),
        # line number the variable occurs on
        Column.LINENO: pd.UInt64Dtype(),
        # number identifying context said variable appears in
        # See TraceDataCategory for more information
        Column.CATEGORY: pd.Int64Dtype(),
        # name of the variableor, when CATEGORY indicates a FUNCTION_RETURN,
        # it is the name of the returning function
        # never None
        Column.VARNAME: pd.StringDtype(),
        # the module of the variable's type
        # None if it is a builtin type
        Column.VARTYPE_MODULE: pd.StringDtype(),
        # the name of the variable's type
        # never None
        Column.VARTYPE: pd.StringDtype(),
    }

    TypeHintData = {
        Column.FILENAME: pd.StringDtype(),
        Column.CLASS: pd.StringDtype(),
        Column.FUNCNAME: pd.StringDtype(),
        Column.COLUMN_OFFSET: pd.UInt64Dtype(),
        Column.CATEGORY: pd.Int64Dtype(),
        Column.VARNAME: pd.StringDtype(),
        Column.VARTYPE: pd.StringDtype(),
    }

    Metrics = {
        Column.FILENAME: pd.StringDtype(),
        Column.CLASS: pd.StringDtype(),
        Column.FUNCNAME: pd.StringDtype(),
        Column.COLUMN_OFFSET: pd.UInt64Dtype(),
        Column.CATEGORY: pd.Int64Dtype(),
        Column.VARNAME: pd.StringDtype(),
        Column.VARTYPE_ORIGINAL: pd.StringDtype(),
        Column.VARTYPE_GENERATED: pd.StringDtype(),
        Column.COMPLETENESS: pd.BooleanDtype(),
        Column.CORRECTNESS: pd.BooleanDtype(),
    }
