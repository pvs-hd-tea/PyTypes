import pathlib
from unittest import mock
import numpy as np
from tracing import decorators
from constants import TraceData


@decorators.register()
def trace_function():
    return f"More"


class Class:
    @decorators.register()
    def trace_method(self):
        return f"Something"


def main():
    ...


def test_everything_is_traced():
    folder_sample_cfg = pathlib.Path("./tests/resource/configs/decorators")
    with mock.patch('pathlib.Path.cwd', return_value=folder_sample_cfg) as _:
        trace_data, performance_data = decorators.entrypoint(folder_sample_cfg)(main)
        assert trace_data is not None
        assert "trace_method" in trace_data[TraceData.FUNCNAME].values
        assert "trace_function" in trace_data[TraceData.FUNCNAME].values

        assert performance_data is None


def test_everything_is_traced_with_benchmark_performance():
    folder_sample_cfg = pathlib.Path("./tests/resource/configs/decorators/with_benchmark_performance")
    with mock.patch('pathlib.Path.cwd', return_value=folder_sample_cfg) as _:
        trace_data, performance_data = decorators.entrypoint(folder_sample_cfg)(main)
        assert trace_data is not None
        assert "trace_method" in trace_data[TraceData.FUNCNAME].values
        assert "trace_function" in trace_data[TraceData.FUNCNAME].values

        assert (performance_data.shape == np.array([2, 4])).all()
