import logging
import pathlib
import pytest

from tracing import register, entrypoint

DUMMY = pathlib.Path("dummy")

def test_mocking_works():
    def mocked_value() -> int:
        return 5

    @register(DUMMY, DUMMY, DUMMY)
    def my_test_f(mocked_value):
        logging.debug(mocked_value)
        assert mocked_value == 5
        
    def working():
        ...

    try:
        entrypoint(None)(working)
    except:
        pytest.fail(f"{working.__name__} should not have failed")

def test_fails_when_mock_not_found():
    def mocked_value() -> int:
        return 5

    @register(DUMMY, DUMMY, DUMMY)
    def bad_test_f(something_else):
        assert something_else == 5

    def not_working():
        ...

    try:
        entrypoint(None)(not_working)
        pytest.fail(f"{not_working.__name__} should have failed")    
    except ValueError:
        pass
    
