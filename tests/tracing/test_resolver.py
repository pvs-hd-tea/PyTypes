import fractions
import importlib
import os
import sys
import pathlib
from types import NoneType

import pytest

from tracing.resolver import Resolver


@pytest.fixture
def resolver():
    proj_path = pathlib.Path.cwd()
    stdlib_path = pathlib.Path(pathlib.__file__).parent
    venv_path = pathlib.Path(os.environ["VIRTUAL_ENV"])

    sys.modules[__name__] = importlib.import_module(__name__)

    return Resolver(
        proj_path=proj_path.resolve(),
        stdlib_path=stdlib_path.resolve(),
        venv_path=venv_path.resolve(),
    )


@pytest.mark.parametrize(
    ("ty", "module", "name"),
    [(int, None, "int"), (str, None, "str"), (NoneType, None, "NoneType")],
)
def test_builtin(resolver: Resolver, ty: type, module: str, name: str):
    assert resolver.get_module_and_name(ty) == (module, name)
    assert resolver.type_lookup(module, name) == ty


# https://stackoverflow.com/questions/46708659/isinstance-fails-for-a-type-imported-via-package-and-from-the-same-module-direct
@pytest.mark.parametrize(
    ("ty", "module", "name"),
    [(pathlib.Path, "pathlib", "Path"), (fractions.Fraction, "fractions", "Fraction")],
)
def test_stdlib(resolver: Resolver, ty: type, module: str, name: str):
    assert resolver.get_module_and_name(ty) == (module, name)
    assert resolver.type_lookup(module, name).__name__ == ty.__name__


class UserClass:
    ...


class Outer:
    class Inner:
        ...


@pytest.mark.parametrize(
    ("ty", "module", "name"),
    [
        (UserClass, "tests.tracing.test_resolver", "UserClass"),
        (Outer.Inner, "tests.tracing.test_resolver", "Outer.Inner"),
    ],
)
def test_proj(resolver: Resolver, ty: type, module: str, name: str):
    assert resolver.get_module_and_name(ty) == (module, name)
    assert resolver.type_lookup(module, name).__name__ == ty.__name__
