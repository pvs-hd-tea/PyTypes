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
    called = decorators.entrypoint(None)(main)
    assert called is not None

    assert "trace_method" in called[TraceData.FUNCNAME].values
    assert "trace_function" in called[TraceData.FUNCNAME].values
