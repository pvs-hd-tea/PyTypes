import logging
import pathlib

# Adapted from https://docs.pytest.org/en/6.2.x/monkeypatch.html?highlight=mocking

from tracing import register, entrypoint

# contents of test_module.py with source code and the test
def getssh():
    """Simple function to return expanded homedir ssh path."""
    return pathlib.Path.home() / ".ssh"


@register()
def mp_getssh(monkeypatch) -> bool:    
    # Application of the monkeypatch to replace Path.home
    # with the behavior to replace Path.home
    # always return '/abc'
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/abc"))

    # Calling getssh() will use mockreturn in place of Path.home
    # for this test with the monkeypatch.
    x = getssh()
    assert x == pathlib.Path("/abc/.ssh")

def test_mocked_getssh():
    # This test passes when the assert above succeeds
    traced, _ = entrypoint()(lambda: None)
    logging.debug(f"{traced}")
    assert True