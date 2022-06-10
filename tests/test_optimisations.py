from .samples import optimisable
import pathlib
from tracing import Tracer, TraceDataCategory

import logging
logging.basicConfig(level=logging.DEBUG)

from unittest.mock import MagicMock, patch

def test_ignore():
    t = Tracer(pathlib.Path.cwd())
    with t.active_trace():
        optimisable.ignorable()
    df = t.trace_data
    print(df)