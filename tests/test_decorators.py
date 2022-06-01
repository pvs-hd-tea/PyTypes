import pathlib

from tracing import entrypoint, register, Tracer
import constants

def test_tracer_attribute_exists():
    @register()
    def another_test_fn():
        return 0

    assert hasattr(another_test_fn, constants.TRACER_ATTRIBUTE)
    assert isinstance(getattr(another_test_fn, constants.TRACER_ATTRIBUTE), Tracer)

