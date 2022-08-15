import pathlib
from typing import Callable

import constants
from tracing import ptconfig
from tracing.tracer import NoOperationTracer, Tracer


def register():
    """
    Register a test function for tracing and performance benchmarking.
    """

    def impl(test_function: Callable[[], None]):
        root = pathlib.Path.cwd()
        cfg = ptconfig.load_config(root / constants.CONFIG_FILE_NAME)
        if cfg.pytypes.proj_path != root:
            raise RuntimeError(
                f"Invalid config file: wrong project root: {register.__name__} had \
                {root} specified, config file has {cfg.pytypes.proj_path} set"
            )

        if not cfg.pytypes.benchmark_performance:
            tracer = Tracer(
                proj_path=root,
                stdlib_path=cfg.pytypes.stdlib_path,
                venv_path=cfg.pytypes.venv_path,
            )

            setattr(test_function, constants.TRACER_ATTRIBUTE, [tracer])

        else:
            no_operation_tracer = NoOperationTracer(
                proj_path=root,
                stdlib_path=cfg.pytypes.stdlib_path,
                venv_path=cfg.pytypes.venv_path,
            )
            standard_tracer = Tracer(
                proj_path=root,
                stdlib_path=cfg.pytypes.stdlib_path,
                venv_path=cfg.pytypes.venv_path,
                apply_opts=False,
            )
            optimized_tracer = Tracer(
                proj_path=root,
                stdlib_path=cfg.pytypes.stdlib_path,
                venv_path=cfg.pytypes.venv_path,
                apply_opts=True,
            )
            setattr(
                test_function,
                constants.TRACERS_ATTRIBUTE,
                [no_operation_tracer, standard_tracer, optimized_tracer],
            )
        return test_function

    return impl
