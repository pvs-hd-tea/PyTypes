from dataclasses import dataclass
import pathlib
from typing import Any, Callable, Protocol, TypeVar
import timeit

import pandas as pd
import numpy as np

import constants
from tracing import ptconfig
from tracing.tracer import NoOperationTracer, Tracer

RetType = TypeVar("RetType")


def _add_tracers_to_callable(
    c: Callable[..., RetType], config: ptconfig.TomlCfg
) -> Callable[..., RetType]:
    if not config.pytypes.benchmark_performance:
        tracer = Tracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
            apply_opts=True,
        )

        setattr(c, constants.TRACERS_ATTRIBUTE, [tracer])

    else:
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
        setattr(
            c,
            constants.TRACERS_ATTRIBUTE,
            [no_operation_tracer, standard_tracer, optimized_tracer],
        )

    return c


@dataclass
class TemplateSubstitutes:
    project: str
    test_case: str
    func_name: str


def _trace_callable(tracer: Tracer, call: Callable[..., RetType]):
    with tracer.active_trace():
        call()


def _execute_tracing(
    c: Callable[..., RetType],
    config: ptconfig.TomlCfg,
    subst: TemplateSubstitutes,
    *args,
    **kwargs,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    # Execute the optimised tracer, which, according to `_add_tracers_to_callable`
    # is always the last element in the tracer attribute on the marked callable
    trace_subst = config.pytypes.output_template.format_map(
        {
            "project": subst.project,
            "test_case": subst.test_case,
            "func_name": subst.func_name,
        }
    )

    benchmark_subst = config.pytypes.output_npy_template.format_map(
        {
            "project": subst.project,
            "test_case": subst.test_case,
            "func_name": subst.func_name,
        }
    )

    tracers: list[Tracer] = getattr(c, constants.TRACERS_ATTRIBUTE)
    tracer: Tracer = tracers[-1]

    _trace_callable(tracer, lambda: c(*args, **kwargs))

    trace_output_path = config.pytypes.proj_path / trace_subst
    traced = tracer.trace_data.copy()
    traced.to_pickle(str(trace_output_path))

    if config.pytypes.benchmark_performance:
        benchmarks = np.zeros((1 + len(tracers)))

        # Reset optimised tracer
        tracers[-1] = Tracer(
            proj_path=config.pytypes.proj_path,
            stdlib_path=config.pytypes.stdlib_path,
            venv_path=config.pytypes.venv_path,
            apply_opts=True,
        )

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

        benchmark_output_path = config.pytypes.proj_path / benchmark_subst
        benchmark_output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(benchmark_output_path, benchmarks)

    else:
        benchmarks = None

    return traced, benchmarks


class _Callback(Protocol):
    def __call__(
        self, *args: Any, **kwds: Any
    ) -> tuple[pd.DataFrame, np.ndarray | None]:
        ...


def trace(c: Callable[..., RetType]) -> _Callback:
    """
    Execute the tracer upon a callable marked with this decorator.
    Supports performance benchmarking when specified in the config file
    """

    def wrapper(*args, **kwargs) -> tuple[pd.DataFrame, np.ndarray | None]:
        root = pathlib.Path.cwd()
        cfg = ptconfig.load_config(root / constants.CONFIG_FILE_NAME)
        if cfg.pytypes.proj_path != root:
            raise RuntimeError(
                f"Invalid config file: wrong project root: {trace.__name__} had \
                {root} specified, config file has {cfg.pytypes.proj_path} set"
            )

        c = _add_tracers_to_callable(c, cfg)
        return _execute_tracing(c, cfg, *args, **kwargs)

    return wrapper
