import pathlib
from typing import Callable

import pandas as pd

from .tracer import Tracer


def hook(test_function: Callable[[], None], root: pathlib.Path | None = None):
    def impl() -> pd.DataFrame:
        tracer = Tracer(base_directory=root or pathlib.Path.cwd())
        tracer.start_trace()
        test_function()
        tracer.stop_trace()

        return tracer.trace_data

    df = impl()
    print(df)