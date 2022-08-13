import inspect
import pathlib
from typing import Callable
import numpy as np
from timeit import default_timer
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
