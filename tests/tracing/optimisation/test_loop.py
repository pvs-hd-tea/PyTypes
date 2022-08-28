import logging
import os
import pathlib


import pandas as pd
from common import TraceDataCategory

from tracing.tracer import Tracer
from constants import Schema


def skippable_looping():
    s = 0
    for x in range(10):
        if x % 2 == 0:
            s += x
    r = s + 10
    return r


def skippable_looping_with_skipped_variable():
    s = 0
    for x in range(100):
        if x > 50:
            forgetme = x
            del forgetme
        if x % 2 == 0:
            s += x
    r = s + 10
    return r


proj_path = pathlib.Path.cwd()
stdlib_path = pathlib.Path(pathlib.__file__).parent
venv_path = pathlib.Path(os.environ["VIRTUAL_ENV"])

test_path = pathlib.Path("tests", "tracing", "optimisation", "test_loop.py")


def test_all_variables_exist():
    tracer = Tracer(proj_path, stdlib_path, venv_path)

    tracer.start_trace()
    skippable_looping()
    tracer.stop_trace()

    df = tracer.trace_data
    print(df)

    expected = pd.DataFrame(columns=Schema.TraceData.keys())
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping",
        14,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping",
        15,
        TraceDataCategory.LOCAL_VARIABLE,
        "x",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping",
        17,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping",
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "r",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "skippable_looping",
        None,
        "int",
    ]
    expected = expected.astype(Schema.TraceData)
    df = df.astype(Schema.TraceData)

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{df}")
    logging.debug(f"diff: \n{expected.compare(df)}")


def test_variable_is_not_traced():
    tracer = Tracer(proj_path, stdlib_path, venv_path)

    tracer.start_trace()
    skippable_looping_with_skipped_variable()
    tracer.stop_trace()

    expected = pd.DataFrame(columns=Schema.TraceData.keys())

    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        23,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        24,
        TraceDataCategory.LOCAL_VARIABLE,
        "x",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        29,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "int",
    ]
    # Special case: s exists when we hit the loop head
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        24,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        30,
        TraceDataCategory.LOCAL_VARIABLE,
        "r",
        None,
        "int",
    ]
    expected.loc[len(expected.index)] = [
        str(test_path),
        None,
        None,
        "skippable_looping_with_skipped_variable",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "skippable_looping_with_skipped_variable",
        None,
        "int",
    ]

    expected = expected.astype(Schema.TraceData)

    df = tracer.trace_data
    df = df.astype(Schema.TraceData)

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{df}")
    assert expected.equals(df)
