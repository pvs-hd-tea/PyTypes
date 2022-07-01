import pathlib, logging
from tracing.tracer import Tracer

import pandas as pd


def call_to_standard_library():
    import pathlib

    b = 1 + 1 # Traced

    p = pathlib.Path("really", "cool", "file.backup")  # Do not trace
    p2 = pathlib.Path("another", "really", "cool", "file.backup")  # Tracing is turned off for this constructor now

    d = p.is_dir()  # Do not trace

    return p.is_file() - bool(b) + d  # Call is not traced, return type is
    return True


def test_pathlib_calls_are_not_traced():
    test_path = pathlib.Path.cwd() / "tests" / "tracing" / "optimisation"
    tracer = Tracer(test_path)

    tracer.start_trace()
    call_to_standard_library()
    tracer.stop_trace()

    df = tracer.trace_data

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(df)

    assert False