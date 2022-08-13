from tracing import decorators
from constants import TraceData
import numpy as np


@decorators.register_performance()
def trace_function():
    return f"More"


class Class:
    @decorators.register_performance()
    def trace_method(self):
        return f"Something"


def main():
    ...


def test_everything_is_traced():
    trace_data, performance_data = decorators.entrypoint(None)(main)
    assert trace_data is not None

    assert "trace_method" in trace_data[TraceData.FUNCNAME].values
    assert "trace_function" in trace_data[TraceData.FUNCNAME].values

    assert (performance_data.shape == np.array([2, 3])).all()
