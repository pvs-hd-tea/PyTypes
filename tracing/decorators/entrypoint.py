import collections
import inspect
import itertools
import logging
import pathlib
import types
import typing
import timeit

import numpy as np
import pandas as pd
from _pytest.monkeypatch import MonkeyPatch

import constants
from tracing import ptconfig
from tracing.tracer import Tracer


def _load_mocks(
    func: typing.Callable, lookup: typing.Mapping, is_method: bool
) -> dict | None:
    signature = inspect.signature(func)
    mocks = dict()

    # skip self
    if is_method:
        params = itertools.islice(signature.parameters, 1, None)
    else:
        params = itertools.islice(signature.parameters, None)

    for param in params:
        if param == "monkeypatch":
            mocks[param] = MonkeyPatch()
    return mocks


def _method_predicate(m: object) -> bool:
    return inspect.isroutine(m) and hasattr(m, constants.TRACERS_ATTRIBUTE)


def entrypoint(proj_root: pathlib.Path | None = None):
    """
    Execute and trace all registered test functions in the same module as the marked function.
    If cfg.benchmark_performance is True, additionally benchmark the performance.
    @param proj_root the path to project's root directory, which contains `pytypes.toml`
    """
    root = proj_root or pathlib.Path.cwd()
    cfg = ptconfig.load_config(root / constants.CONFIG_FILE_NAME)

    def impl(
        main: typing.Callable[..., None]
    ) -> tuple[pd.DataFrame | None, np.ndarray | None]:
        main()
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

        trace_dataframes = list()
        performance_arrays = list()

        # https://docs.python.org/3/library/collections.html#collections.ChainMap clearly exists?
        search_space = collections.ChainMap(prev_frame.f_locals, prev_frame.f_globals)  # type: ignore
        classes_with_callables: list[
            tuple[type | None, types.FunctionType | types.MethodType]
        ] = []

        # Searches for registered functions/methods.
        for entity in search_space.values():
            if inspect.isfunction(entity) and hasattr(
                entity, constants.TRACERS_ATTRIBUTE
            ):
                logging.debug(f"Found registered function {entity.__name__}")
                classes_with_callables.append((None, entity))

            if inspect.isclass(entity):
                for _, method in inspect.getmembers(
                    entity, predicate=_method_predicate
                ):
                    logging.debug(
                        f"Found registered method {entity.__name__}.{method.__name__}"
                    )
                    classes_with_callables.append((entity, method))

        module = inspect.getmodule(prev_frame)
        assert module is not None  # we can never come from a builtin
        module_name = module.__name__

        # Traces each registered function/method.
        for clazz, registered_call in classes_with_callables:
            registered_call_mocks = _load_mocks(
                registered_call, search_space, clazz is not None
            )

            callable_name = (
                registered_call.__name__
                if not clazz
                else f"{clazz.__name__}@{registered_call.__name__}"
            )
            if registered_call_mocks is None:
                sig = inspect.signature(registered_call)
                raise ValueError(f"Failed to load mocks for {callable_name}{sig}")

            substituted_output = cfg.pytypes.output_template.format_map(
                {
                    "project": cfg.pytypes.project,
                    "test_case": module_name,
                    "func_name": callable_name,
                }
            )

            trace_data = _generate_and_serialize_trace_data(
                clazz, registered_call, registered_call_mocks, substituted_output
            )
            trace_dataframes.append(trace_data)

            if cfg.pytypes.benchmark_performance:
                substituted_output_performance_data = (
                    cfg.pytypes.output_npy_template.format_map(
                        {
                            "project": cfg.pytypes.project,
                            "test_case": module_name,
                            "func_name": callable_name,
                        }
                    )
                )
                performance_data = _generate_and_serialize_performance_data(
                    clazz,
                    registered_call,
                    registered_call_mocks,
                    substituted_output_performance_data,
                )
                performance_arrays.append(performance_data)

        return (
            pd.concat(trace_dataframes) if trace_dataframes else None,
            np.array(performance_arrays) if performance_arrays else None,
        )

    return impl


def _generate_and_serialize_trace_data(
    clazz: type | None,
    registered_call: typing.Callable,
    mocks: dict,
    substituted_output: str,
) -> pd.DataFrame:
    tracers: list[Tracer] = getattr(registered_call, constants.TRACERS_ATTRIBUTE)

    # Find tracer meant for standard benchmarking.
    # According to the implementation of @register, it is always in the last position
    tracer = tracers[-1]

    output_path: pathlib.Path = tracer.proj_path / substituted_output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if clazz is None:
        with tracer.active_trace():
            registered_call(**mocks)
    else:
        instance: typing.Any = object.__new__(clazz)
        with tracer.active_trace():
            registered_call(instance, **mocks)
    tracer.trace_data.to_pickle(str(output_path))
    return tracer.trace_data


def _generate_and_serialize_performance_data(
    clazz: type | None,
    registered_call: typing.Callable,
    mocks: dict,
    substituted_output: str,
) -> np.ndarray:
    tracers: list[Tracer] = getattr(registered_call, constants.TRACERS_ATTRIBUTE)
    measured_times = np.zeros((1 + len(tracers)))

    # test setup
    if clazz is None:
        registered_with_mocks = lambda: registered_call(**mocks)  # noqa: E731
    else:
        instance: typing.Any = object.__new__(clazz)
        registered_with_mocks = lambda: registered_call(instance, **mocks)  # noqa: E731

    measured_times[0] = timeit.timeit(
        registered_with_mocks, number=constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE
    )

    for i, tracer in enumerate(tracers):
        measured_times[i + 1] = timeit.timeit(
            lambda: _trace_callable(tracer, registered_with_mocks),
            number=constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE,
        )

    proj_path = tracers[0].proj_path
    output_path = proj_path / substituted_output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    np.save(output_path, measured_times)
    return measured_times


def _trace_callable(tracer: Tracer, call: typing.Callable[[], typing.Any]):
    with tracer.active_trace():
        call()
