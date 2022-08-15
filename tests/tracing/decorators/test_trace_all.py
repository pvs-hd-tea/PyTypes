import pathlib
from pydoc import resolve

import numpy as np

from tracing import decorators, ptconfig
from constants import TraceData

MOCK_PATH = pathlib.Path("tests", "tracing", "decorators")


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
                benchmark_performance=True
            )
        ),
    )

    @decorators.register()
    def trace_function():
        return f"More"

    class Class:
        @decorators.register()
        def trace_method(self):
            return f"Something"

    trace_data, performance_data = decorators.entrypoint()(lambda: ...)
    assert trace_data is not None
    assert "trace_method" in trace_data[TraceData.FUNCNAME].values
    assert "trace_function" in trace_data[TraceData.FUNCNAME].values

    assert (
        performance_data.shape == np.array([2, 4])
    ).all(), f"Performance data shape check failed!, got {performance_data.shape}"


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
            )
        ),
    )

    @decorators.register()
    def trace_function():
        return f"More"

    class Class:
        @decorators.register()
        def trace_method(self):
            return f"Something"

    trace_data, performance_data = decorators.entrypoint()(lambda: ...)
    assert trace_data is not None
    assert "trace_method" in trace_data[TraceData.FUNCNAME].values
    assert "trace_function" in trace_data[TraceData.FUNCNAME].values

    assert performance_data is None
