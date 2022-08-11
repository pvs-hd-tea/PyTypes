import logging
import os
import pathlib
import sys

import pandas as pd
from tracing.trace_data_category import TraceDataCategory

from tracing.tracer import Tracer
import constants

# NOTE: Ignored has been made defunct;
# NOTE: the tracer will ignore the pathlib calls by itself


def call_to_standard_library():
    import pathlib

    b = 1 + 1  # Traced

    p = pathlib.Path("really", "cool", "file.backup")  # Do not trace
    p2 = pathlib.Path(
        "another", "really", "cool", "file.backup"
    )  # Tracing is turned off for this constructor now

    d = p.is_dir()  # Do not trace

    return p.is_file() - bool(b) + d  # Call is not traced, return type is


proj_path = pathlib.Path.cwd()
import pathlib
stdlib_path = pathlib.Path(pathlib.__file__).parent
venv_path = pathlib.Path(os.environ["VIRTUAL_ENV"])


def test_pathlib_calls_are_not_traced():
    resource_path = pathlib.Path.cwd() / "tests" / "tracing" / "optimisation"
    tracer = Tracer(proj_path, stdlib_path, venv_path)

    tracer.start_trace()
    call_to_standard_library()
    tracer.stop_trace()

    df = tracer.trace_data
    print(df)

    assert df.shape[0] == 6

    expected = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        17,
        TraceDataCategory.LOCAL_VARIABLE,
        "pathlib",
        None,
        "module",
    ]

    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        19,
        TraceDataCategory.LOCAL_VARIABLE,
        "b",
        None,
        "int",
    ]

    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "p",
        "pathlib",
        "Path",
    ]

    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        22,
        TraceDataCategory.LOCAL_VARIABLE,
        "p",
        "pathlib",
        "Path",
    ]

    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        26,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        None,
        "bool",
    ]

    expected.loc[len(expected.index)] = [
        str(resource_path),
        None,
        None,
        "call_to_standard_library",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "call_to_standard_library",
        None,
        "int",
    ]

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{df}")
    logging.debug(f"diff: \n{expected.compare(df)}")
