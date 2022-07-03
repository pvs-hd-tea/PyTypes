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


def test_pathlib_calls_are_not_traced():
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
        (skippable_looping.__name__, int),
    ]

    for (name, _) in vars:
        assert name in df[constants.TraceData.VARNAME].values
