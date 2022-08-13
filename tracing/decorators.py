import collections
import inspect
import pathlib
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


def entrypoint(proj_root: pathlib.Path | None = None) -> Callable[..., pd.DataFrame | None]:
    """
    Execute and trace all registered test functions in the same module as the marked function
    @param proj_root the path to project's root directory, which contains `pytypes.toml`
    """
    root = proj_root or pathlib.Path.cwd()
    cfg = load_config(root / constants.CONFIG_FILE_NAME)

    def _load_mocks_for_func(func: Callable, lookup: Mapping) -> dict | None:
        signature = inspect.signature(func)
        mocks = dict()

        for param in signature.parameters:
            glob = lookup.get(param)
            # Mocks are usually callables
            if glob is None or not inspect.isfunction(glob):
                return None
            mocks[param] = glob()

        return mocks

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
        for fname, function in searchable.items():
            if not inspect.isfunction(function) or not hasattr(
                function, constants.TRACER_ATTRIBUTE
            ):
                continue

            else:
                substituted_output = cfg.pytypes.output_template.format_map(
                    {"project": cfg.pytypes.project, "func_name": fname}
                )

                tracer: Tracer = getattr(function, constants.TRACER_ATTRIBUTE)
                output_path: pathlib.Path = tracer.proj_path / substituted_output
                output_path.parent.mkdir(parents=True, exist_ok=True)

                mocks = _load_mocks_for_func(function, searchable)
                if mocks is None:
                    sig = inspect.signature(function)
                    raise ValueError(
                        f"Failed to load mocks for {function.__name__}{sig}"
                    )

                with tracer.active_trace():
                    function(**mocks)

                tracer.trace_data.to_pickle(str(output_path))
                dfs.append(tracer.trace_data)

        return pd.concat(dfs) if dfs else None

    return impl
