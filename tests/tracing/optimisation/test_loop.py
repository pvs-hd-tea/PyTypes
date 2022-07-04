import pathlib

import pandas as pd

from tracing.tracer import Tracer
import constants


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
        if x % 2 == 0:
            s += x

        if x > 50:
            forgetme = x
    r = s + 10
    return r


def test_all_variables_exist():
    test_path = pathlib.Path.cwd() / "tests" / "tracing" / "optimisation"
    tracer = Tracer(test_path)

    tracer.start_trace()
    skippable_looping()
    tracer.stop_trace()

    df = tracer.trace_data

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(df)

    vars = [
        ("s", int),
        ("x", int),
        ("r", int),
        (skippable_looping.__name__, int),
    ]
    assert df.shape[0] == len(vars)

    for (name, _) in vars:
        assert name in df[constants.TraceData.VARNAME].values



def test_variable_is_not_traced():
    test_path = pathlib.Path.cwd() / "tests" / "tracing" / "optimisation"
    tracer = Tracer(test_path)

    tracer.start_trace()
    test_all_variables_exist()
    tracer.stop_trace()

    df = tracer.trace_data

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(df)

    assert "forgetme" not in df[constants.TraceData.VARNAME].values
