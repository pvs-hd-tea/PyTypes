from dataclasses import dataclass
import functools
import os
import pathlib
import inspect
from typing import Any, Callable, Protocol, TypeVar
import timeit

import pandas as pd
import numpy as np

import constants
from tracing import ptconfig
from tracing.tracer import NoOperationTracer, Tracer, TracerBase

RetType = TypeVar("RetType")


@dataclass
class _TemplateSubstitutes:
    project: str
    test_case: str
    func_name: str


def _trace_callable(tracer: TracerBase, call: Callable[..., RetType]):
    with tracer.active_trace():
        call()


def _execute_tracing(
    c: Callable[..., RetType],
    config: ptconfig.TomlCfg,
    subst: _TemplateSubstitutes,
    *args,
    **kwargs,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    trace_subst = config.pytypes.output_template.format_map(
        {
            "project": subst.project,
            "test_case": subst.test_case,
            "func_name": subst.func_name,
        }
    )

    if config.pytypes.benchmark_performance:
        benchmark_subst = config.pytypes.output_npy_template.format_map(
            {
                "project": subst.project,
                "test_case": subst.test_case,
                "func_name": subst.func_name,
            }
        )

        no_operation_tracer = NoOperationTracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
        )
        standard_tracer = Tracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
            apply_opts=False,
        )
        optimized_tracer = Tracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
            apply_opts=True,
        )

        tracers: list[TracerBase] = [
            no_operation_tracer,
            standard_tracer,
            optimized_tracer,
        ]
        benchmarks = np.zeros((1 + len(tracers)))

        # bare bones benchmark execution
        benchmarks[0] = timeit.timeit(
            lambda: c(*args, **kwargs),
            number=constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE,
        )

        for i, tracer in enumerate(tracers):
            benchmarks[i + 1] = timeit.timeit(
                lambda: _trace_callable(tracer, lambda: c(*args, **kwargs)),
                number=constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE,
            )

        traced = tracers[-1].trace_data

    else:
        benchmarks = None

        tracer = Tracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
            apply_opts=True,
        )

        _trace_callable(tracer, lambda: c(*args, **kwargs))

        traced = tracer.trace_data

    if benchmarks is not None:
        benchmark_output_path = config.pytypes.proj_path / benchmark_subst
        benchmark_output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(benchmark_output_path, benchmarks)

    trace_output_path = config.pytypes.proj_path / trace_subst
    print(trace_output_path)
    trace_output_path.parent.mkdir(parents=True, exist_ok=True)
    traced.to_pickle(str(trace_output_path))

    return traced, benchmarks


class _Traceable(Protocol):
    def __call__(
        self, *args: Any, **kwds: Any
    ) -> tuple[pd.DataFrame, np.ndarray | None]:
        pass


def trace(c: Callable[..., RetType]) -> _Traceable:
    """
    Execute the tracer upon a callable marked with this decorator.
    Supports performance benchmarking when specified in the config file
    """
    current_frame = inspect.currentframe()
    if current_frame is None:
        raise RuntimeError(
            "inspect.currentframe returned None, unable to trace execution!"
        )

    prev_frame = current_frame.f_back
    if prev_frame is None:
        raise RuntimeError(
            "The current stack frame has no predecessor, unable to trace execution!"
        )

    module = inspect.getmodule(prev_frame)
    assert module is not None  # we can never come from a builtin
    module_name = module.__name__.replace(".", os.path.sep)

    @functools.wraps(c)
    def wrapper(*args, **kwargs) -> tuple[pd.DataFrame, np.ndarray | None]:
        root = pathlib.Path.cwd()
        cfg = ptconfig.load_config(root / constants.CONFIG_FILE_NAME)
        if cfg.pytypes.proj_path != root:
            raise RuntimeError(
                f"Invalid config file: wrong project root: {trace.__name__} had \
                {root} specified, config file has {cfg.pytypes.proj_path} set"
            )

        subst = _TemplateSubstitutes(
            project=cfg.pytypes.project,
            test_case=module_name,
            func_name=c.__name__,
        )
        return _execute_tracing(c, cfg, subst, *args, **kwargs)

    return wrapper
