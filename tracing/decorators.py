from contextlib import contextmanager
from dataclasses import dataclass, field
import functools
import inspect
import sys
import os, pathlib
from typing import Callable

import pandas as pd
import dacite, toml

from .tracer import Tracer
import constants


@dataclass
class Config:
    project: str
    output_template: str = field(default="{project}-{func_name}.pytype")


def _load_config(config_path: pathlib.Path) -> Config:
    cfg = toml.load(config_path.open())
    return dacite.from_dict(Config, cfg)


def register(proj_root: pathlib.Path | None = None):
    """
    Register a test function for tracing.
    @param proj_root the path to project's root directory
    """

    def impl(test_function: Callable[[], None]):
        test_function.pytype_trace = Tracer(project_dir=proj_root or pathlib.Path.cwd())
        return test_function

    return impl


def entrypoint(proj_root: pathlib.Path | None = None):
    """
    Execute and trace all registered test functions in the same module as the marked function
    @param proj_root the path to project's root directory, which contains `pytypes.toml`
    """
    root = proj_root or pathlib.Path.cwd()
    cfg = _load_config(root / "pytypes.toml")

    def impl(main: Callable[[], None]):
        main()
        prev_frame = inspect.currentframe().f_back

        for fname, function in prev_frame.f_globals.items():
            if not inspect.isfunction(function) or not hasattr(
                function, constants.CONFIG_FILE_NAME
            ):
                continue

            substituted_output = cfg.output_template.format_map(
                {"project": cfg.project, "func_name": fname}
            )
            tracer = function.pytype_trace

            with tracer.active_trace():
                function()

            tracer.trace_data.to_pickle(str(tracer.basedir / substituted_output))

    return impl
