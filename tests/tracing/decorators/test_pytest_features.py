import os
import pathlib
import pytest
from tests.tracing.decorators.test_trace_all import MOCK_PATH

from tracing import decorators
from common import ptconfig

MOCK_PATH = pathlib.Path.cwd()


@pytest.fixture
def cfg(monkeypatch) -> ptconfig.TomlCfg:
    monkeypatch.setattr(
        pathlib.Path, pathlib.Path.cwd.__name__, lambda: MOCK_PATH.resolve()
    )
    monkeypatch.setattr(
        ptconfig,
        ptconfig.load_config.__name__,
        lambda _: ptconfig.TomlCfg(
            pytypes=ptconfig.PyTypes(
                project="pytest-mocks",
                proj_path=MOCK_PATH,
                venv_path=pathlib.Path(os.environ["VIRTUAL_ENV"]),
                stdlib_path=pathlib.Path(pathlib.__file__).parent,
            ),
            unifier=list(),
        ),
    )


##### MONKEYPATCHING #####

# Adapted from https://docs.pytest.org/en/6.2.x/monkeypatch.html?highlight=mocking
# contents of test_module.py with source code and the test
def getssh():
    """Simple function to return expanded homedir ssh path."""
    return pathlib.Path.home() / ".ssh"


@decorators.trace
def test_monkeypatched_getssh(monkeypatch, cfg) -> None:
    # Application of the monkeypatch to replace Path.home
    # with the behavior to replace Path.home
    # always return '/abc'
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/abc"))

    # Calling getssh() will use mockreturn in place of Path.home
    # for this test with the monkeypatch.
    x = getssh()
    assert x == pathlib.Path("/abc/.ssh")


##### PARAMETRIZE #####

# Adapted from https://docs.pytest.org/en/6.2.x/parametrize.html


@pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 54)])
@decorators.trace
def test_eval(test_input, expected, cfg):
    assert eval(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [("3+5", 8), ("2+4", 6), pytest.param("6*9", 42, marks=pytest.mark.xfail)],
)
@decorators.trace
def test_eval(test_input, expected, cfg):
    assert eval(test_input) == expected


@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("y", [2, 3])
@decorators.trace
def test_foo(x, y, cfg):
    assert x in (0, 1) and y in (2, 3)


##### FIXTURES #####

# Adapted from https://docs.pytest.org/en/6.2.x/fixture.html#fixture-parametrize
import smtplib


@pytest.fixture(scope="module", params=["smtp.gmail.com", "mail.python.org"])
def smtp_connection(request):
    smtp_connection = smtplib.SMTP(request.param, 587, timeout=5)
    yield smtp_connection
    print("finalizing {}".format(smtp_connection))
    smtp_connection.close()


class App:
    def __init__(self, smtp_connection):
        self.smtp_connection = smtp_connection


@pytest.fixture(scope="module")
def app(smtp_connection):
    return App(smtp_connection)


@decorators.trace
def test_smtp_connection_exists(app, cfg):
    assert app.smtp_connection
