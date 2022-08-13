import collections
import inspect
import itertools
import logging
import pathlib
import types
from typing import Callable, Mapping

import pandas as pd

from .tracer import Tracer
from .ptconfig import load_config
import constants


def register(
    proj_root: pathlib.Path | None = None,
    stdlib_path: pathlib.Path | None = None,
    venv_path: pathlib.Path | None = None,
):
    """
    Register a test function for tracing.
    @param proj_root the path to project's root directory
    """

    def impl(test_function: Callable[[], None]):
        if proj_root is not None and stdlib_path is not None and venv_path is not None:
            print(
                f"All arguments to the {register.__name__} on {test_function.__name__} \
                were specified; NOT reading from {constants.CONFIG_FILE_NAME}"
            )
            tracer = Tracer(
                proj_path=proj_root,
                stdlib_path=stdlib_path,
                venv_path=venv_path,
            )

        else:
            root = proj_root or pathlib.Path.cwd()
            cfg = load_config(root / constants.CONFIG_FILE_NAME)
            if cfg.pytypes.proj_path != root:
                raise RuntimeError(
                    f"Invalid config file: wrong project root: {register.__name__} had \
                    {root} specified, config file has {cfg.pytypes.proj_path} set"
                )

            chosen_root = root
            chosen_stdlib = stdlib_path or cfg.pytypes.stdlib_path
            chosen_venv = venv_path or cfg.pytypes.venv_path

            tracer = Tracer(
                proj_path=chosen_root,
                stdlib_path=chosen_stdlib,
                venv_path=chosen_venv,
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
        searchable = collections.ChainMap(prev_frame.f_locals, prev_frame.f_globals)  # type: ignore
        callables: list[tuple[type | None, types.FunctionType | types.MethodType]] = []

        for entity in searchable.values():
            if inspect.isfunction(entity) and hasattr(
                entity, constants.TRACER_ATTRIBUTE
            ):
                logging.debug(f"Found registered function {entity.__name__}")
                callables.append((None, entity))

            if inspect.isclass(entity):
                for _, mem in inspect.getmembers(entity, predicate=_method_predicate):
                    logging.debug(f"Found registered method {entity.__name__}.{mem.__name__}")
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

            mocks = _load_mocks(call, searchable, clazz is not None)
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

    return impl
