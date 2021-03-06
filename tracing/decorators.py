import inspect
import pathlib
from typing import Callable


from .tracer import Tracer
from .ptconfig import _load_config
import constants


def register(proj_root: pathlib.Path | None = None):
    """
    Register a test function for tracing.
    @param proj_root the path to project's root directory
    """

    def impl(test_function: Callable[[], None]):
        tracer = Tracer(project_dir=proj_root or pathlib.Path.cwd())
        setattr(test_function, constants.TRACER_ATTRIBUTE, tracer)
        return test_function

    return impl


def entrypoint(proj_root: pathlib.Path | None = None):
    """
    Execute and trace all registered test functions in the same module as the marked function
    @param proj_root the path to project's root directory, which contains `pytypes.toml`
    """
    root = proj_root or pathlib.Path.cwd()
    cfg = _load_config(root / constants.CONFIG_FILE_NAME)

    def impl(main: Callable[[], None]):
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

        for fname, function in prev_frame.f_globals.items():
            if not inspect.isfunction(function) or not hasattr(
                function, constants.TRACER_ATTRIBUTE
            ):
                continue

            substituted_output = cfg.pytypes.output_template.format_map(
                {"project": cfg.pytypes.project, "func_name": fname}
            )
            tracer = getattr(function, constants.TRACER_ATTRIBUTE)
            # delattr(function, constants.TRACER_ATTRIBUTE)

            with tracer.active_trace():
                function()

            tracer.trace_data.to_pickle(str(tracer.project_dir / substituted_output))

    return impl
