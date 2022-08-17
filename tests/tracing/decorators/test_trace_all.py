import pathlib
import numpy as np

from tracing import ptconfig, decorators
from constants import TraceData


def trace_function():
    return f"More"


class Class:
    def trace_method(self):
        return f"Something"


MOCK_PATH = pathlib.Path("tests", "tracing", "decorators")


def test_everything_is_traced(monkeypatch):
    monkeypatch.setattr(
        pathlib.Path, pathlib.Path.cwd.__name__, lambda: MOCK_PATH.resolve()
    )
    monkeypatch.setattr(
        ptconfig,
        ptconfig.load_config.__name__,
        lambda _: ptconfig.TomlCfg(
            ptconfig.PyTypes(
                project="standard-trace",
                proj_path=MOCK_PATH.resolve(),
                stdlib_path=pathlib.Path(),
                venv_path=pathlib.Path(),
                benchmark_performance=False,
            )
        ),
    )

    ftrace, fperf = decorators.trace(trace_function)()
    assert fperf is None
    assert ftrace is not None, f"Trace data of {ftrace.__name__} should not be None"
    assert (
        "trace_function" in ftrace[TraceData.FUNCNAME].values
    ), f"Trace data for 'trace_function' is missing from {ftrace.__name__}"

    mtrace, mperf = decorators.trace(Class().trace_method)()
    assert mperf is None
    assert mtrace is not None, f"Trace data of {mtrace.__name__} should not be None"
    assert (
        "trace_method" in mtrace[TraceData.FUNCNAME].values
    ), f"Trace data for 'trace_method' is missing from {mtrace.__name__}"


def test_everything_is_traced_with_benchmark_performance(monkeypatch):
    monkeypatch.setattr(
        pathlib.Path, pathlib.Path.cwd.__name__, lambda: MOCK_PATH.resolve()
    )
    monkeypatch.setattr(
        ptconfig,
        ptconfig.load_config.__name__,
        lambda _: ptconfig.TomlCfg(
            ptconfig.PyTypes(
                project="standard-trace",
                proj_path=MOCK_PATH.resolve(),
                stdlib_path=pathlib.Path(),
                venv_path=pathlib.Path(),
                benchmark_performance=True,
            )
        ),
    )

    ftrace, fperf = decorators.trace(trace_function)()
    assert ftrace is not None, f"Trace data of {ftrace.__name__} should not be None"
    assert (
        "trace_function" in ftrace[TraceData.FUNCNAME].values
    ), f"Trace data for 'trace_function' is missing from {ftrace.__name__}"

    assert (
        fperf is not None
    ), f"When benchmarking, perf data 'fperf': should not be None"
    assert fperf.shape == (4,), f"Wrong benchmark shape for 'fperf': Got {fperf.shape}"

    mtrace, mperf = decorators.trace(Class().trace_method)()
    assert mtrace is not None, f"Trace data of {mtrace.__name__} should not be None"
    assert (
        "trace_method" in mtrace[TraceData.FUNCNAME].values
    ), f"Trace data for 'trace_method' is missing from {mtrace.__name__}"

    assert (
        mperf is not None
    ), f"When benchmarking, perf data 'mperf': should not be None"
    assert mperf.shape == (4,), f"Wrong benchmark shape for 'mperf': Got {mperf.shape}"
