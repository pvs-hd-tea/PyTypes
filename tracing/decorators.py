import collections
import inspect
import itertools
import logging
import pathlib
import types
from typing import Callable, Mapping

import pandas as pd

from typing import Callable
import numpy as np
from timeit import default_timer
from .tracer import Tracer
from .ptconfig import load_config
import constants


def register():
    """
    Register a test function for tracing.
    @param proj_root the path to project's root directory
    """

    def impl(test_function: Callable[[], None]):
        root = pathlib.Path.cwd()
        cfg = load_config(root / constants.CONFIG_FILE_NAME)
        if cfg.pytypes.proj_path != root:
            raise RuntimeError(
                f"Invalid config file: wrong project root: {register.__name__} had \
                {root} specified, config file has {cfg.pytypes.proj_path} set"
            )

        tracer = Tracer(
            proj_path=root,
            stdlib_path=cfg.pytypes.stdlib_path,
            venv_path=cfg.pytypes.venv_path,
        )

        setattr(test_function, constants.TRACER_ATTRIBUTE, tracer)
        return test_function

    return impl


def _load_mocks(func: Callable, lookup: Mapping, is_method: bool) -> dict | None:
    signature = inspect.signature(func)
    mocks = dict()

    # skip self
    if is_method:
        params = itertools.islice(signature.parameters, 1, None)
    else:
        params = itertools.islice(signature.parameters, None)

    for param in params:
        glob = lookup.get(param)
        # Mocks are usually callables
        if glob is None or not inspect.isfunction(glob):
            return None
        mocks[param] = glob()

    return mocks


def _method_predicate(m: object) -> bool:
    return inspect.isroutine(m) and hasattr(m, constants.TRACER_ATTRIBUTE)


def entrypoint(
    proj_root: pathlib.Path | None = None,
) -> Callable[..., pd.DataFrame | None]:
def register_performance(proj_root: pathlib.Path | None = None):
    """
    Register a test function for performance testing.
    @param proj_root the path to project's root directory
    """

    def impl(test_function: Callable[[], None]):
        standard_tracer = Tracer(project_dir=proj_root or pathlib.Path.cwd(), apply_opts=False)
        optimized_tracer = Tracer(project_dir=proj_root or pathlib.Path.cwd(), apply_opts=True)
        setattr(test_function, constants.TRACERS_ATTRIBUTE, [standard_tracer, optimized_tracer])
        return test_function

    return impl


def entrypoint(proj_root: pathlib.Path | None = None):
    """
    Execute and trace all registered test functions in the same module as the marked function
    @param proj_root the path to project's root directory, which contains `pytypes.toml`
    """
    root = proj_root or pathlib.Path.cwd()
    cfg = load_config(root / constants.CONFIG_FILE_NAME)

    def impl(main: Callable[..., None]) -> pd.DataFrame | None:
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

        dfs = list()

        # https://docs.python.org/3/library/collections.html#collections.ChainMap clearly exists?
        search_space = collections.ChainMap(prev_frame.f_locals, prev_frame.f_globals)  # type: ignore
        callables: list[tuple[type | None, types.FunctionType | types.MethodType]] = []

        for entity in search_space.values():
            if inspect.isfunction(entity) and hasattr(
                entity, constants.TRACER_ATTRIBUTE
            ):
                logging.debug(f"Found registered function {entity.__name__}")
                callables.append((None, entity))

            if inspect.isclass(entity):
                for _, mem in inspect.getmembers(entity, predicate=_method_predicate):
                    logging.debug(
                        f"Found registered method {entity.__name__}.{mem.__name__}"
                    )
                    callables.append((entity, mem))

        for clazz, call in callables:
            module = inspect.getmodule(prev_frame)
            assert module is not None  # we can never come from a builtin

            callable_name = (
                call.__name__ if not clazz else f"{clazz.__name__}@{call.__name__}"
            )
            module_name = module.__name__
            substituted_output = cfg.pytypes.output_template.format_map(
                {
                    "project": cfg.pytypes.project,
                    "test_case": module_name,
                    "func_name": callable_name,
                }
            )

            tracer: Tracer = getattr(call, constants.TRACER_ATTRIBUTE)
            output_path: pathlib.Path = tracer.proj_path / substituted_output
            output_path.parent.mkdir(parents=True, exist_ok=True)

            mocks = _load_mocks(call, search_space, clazz is not None)
            if mocks is None:
                sig = inspect.signature(call)
                raise ValueError(f"Failed to load mocks for {callable_name}{sig}")

            if clazz is None:
                with tracer.active_trace():
                    call(**mocks)
            else:
                # tracing/decorators.py: error: Need type annotation for "instance"
                instance = object.__new__(clazz)  # type: ignore
                with tracer.active_trace():
                    call(instance, **mocks)

            tracer.trace_data.to_pickle(str(output_path))
            dfs.append(tracer.trace_data)

        return pd.concat(dfs) if dfs else None

        for fname, function in prev_frame.f_globals.items():
            if not inspect.isfunction(function):
                continue
            if hasattr(
                function, constants.TRACER_ATTRIBUTE
            ):
                substituted_output = cfg.pytypes.output_template.format_map(
                    {"project": cfg.pytypes.project, "func_name": fname}
                )
                tracer = getattr(function, constants.TRACER_ATTRIBUTE)
                # delattr(function, constants.TRACER_ATTRIBUTE)

                with tracer.active_trace():
                    function()

                output_path: pathlib.Path = tracer.project_dir / substituted_output
                output_path.parent.mkdir(parents=True, exist_ok=True)
                tracer.trace_data.to_pickle(str(output_path))
            elif hasattr(
                function, constants.TRACERS_ATTRIBUTE
            ):
                tracers = getattr(function, constants.TRACERS_ATTRIBUTE)
                measured_times = np.zeros((1 + len(tracers), constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE))
                project_dir = tracers[0].project_dir
                for i in range(constants.AMOUNT_EXECUTIONS_TESTING_PERFORMANCE):
                    start_time = default_timer()
                    function()
                    end_time = default_timer()
                    measured_times[0, i] = end_time - start_time
                    for j, tracer in enumerate(tracers):
                        start_time = default_timer()
                        with tracer.active_trace():
                            function()
                        end_time = default_timer()
                        measured_times[1 + j, i] = end_time - start_time
                measured_times_mean = np.mean(measured_times, axis=1)

                substituted_output = cfg.pytypes.output_npy_template.format_map(
                    {"project": cfg.pytypes.project, "func_name": fname}
                )

                np.save(str(project_dir / substituted_output), measured_times_mean)

    return impl
