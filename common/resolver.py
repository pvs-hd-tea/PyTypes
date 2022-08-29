from dataclasses import dataclass
import functools
import importlib.util
from importlib.machinery import SourceFileLoader
import logging
import os
import pathlib
import sys
from types import ModuleType, NoneType

import pandas as pd


logger = logging.getLogger(__name__)


def _attempt_module_lookup(
    module_name: str, root: pathlib.Path, lookup_path: pathlib.Path
) -> ModuleType | None:
    try:
        loader = SourceFileLoader(module_name, str(root / lookup_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)

            sys.modules[module_name] = module
            loader.exec_module(module)
            del sys.modules[module_name]

            logger.debug(f"Imported {module_name} from {str(root / lookup_path)}")
            return module

    except FileNotFoundError:
        logger.warning(f"Could not import {module_name} from {str(root / lookup_path)}")

    return None


@dataclass
class Resolver:
    """
    Bidirectional lookup of types and modules

    :param proj_path: Path to root directory containing the project's types
    :param stdlib_path: Path to standard library's directory of the Python binary, containing stdlib types
    :param venv_path: Path to project's virtual environment's directory containing third-party deps

    :raises ValueError: If any of the three specified paths is not a directory
    """
    stdlib_path: pathlib.Path
    proj_path: pathlib.Path
    venv_path: pathlib.Path

    def __post_init__(self):
        for path in (self.stdlib_path, self.proj_path, self.venv_path):
            if not path.is_dir():
                raise ValueError(
                    f"{path} is not a directory; Please check your config file"
                )

    @functools.cached_property
    def site_packages(self) -> pathlib.Path:
        major, minor = sys.version_info[:2]
        site_packages = (
            self.venv_path / "lib" / f"python{major}.{minor}" / "site-packages"
        )
        if not self.venv_path.is_dir():
            raise ValueError(
                f"Could not find site-packages directory at {site_packages}"
            )
        return site_packages

    def type_lookup(
        self, module_name: str | None | pd._libs.missing.NAType, type_name: str
    ) -> type | None:
        """Create a type from a module path and qualified type name.
        Fails if the given paths lies outside of the module

        :param module_name: The module of the type e.g. pathlib
        :param type_name: The fully qualified name of the type, e.g. Path
        :return: The requested type if found, e.g. pathlib.Path, else None
        """

        # 0. builtin types
        logger.debug(f"{(module_name, type_name)} as builtin?")
        if not isinstance(module_name, str):
            # __builtins__ is typed as Module by mypy, but is dict in the REPL?
            # Special case: NoneType
            if type_name == "NoneType":
                return NoneType
            builtin_ty: type = __builtins__[type_name]  # type: ignore
            return builtin_ty

        else:
            # recreate filename
            lookup_path = pathlib.Path(module_name.replace(".", os.path.sep) + ".py")

            # 1. project path
            logger.debug(f"{(module_name, type_name)} as project path?")
            module = _attempt_module_lookup(module_name, self.proj_path, lookup_path)
            if module is None:
                # 2. stdlib
                logger.debug(f"{(module_name, type_name)} as stdlib?")
                module = _attempt_module_lookup(
                    module_name, self.stdlib_path, lookup_path
                )

            if module is None:
                # 3. venv
                logger.debug(f"{(module_name, type_name)} as venv dep?")
                module = _attempt_module_lookup(
                    module_name, self.site_packages, lookup_path
                )

            if module is None:
                logger.warning(
                    f"Failed to import {module_name} from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
                )
                return None

            # Resolve inner classes too!
            # Have to ignore because mypy thinks accessing a module returns a module :shrug:
            variable_type: type = functools.reduce(getattr, type_name.split("."), module)  # type: ignore
            return variable_type

    def get_module_and_name(self, ty: type) -> tuple[str | None, str] | None:
        """Retrieve module path and qualified type name from a type.
        Fails if the type lies outside of the three paths specified in the constructor.

        :param ty: Any given type whose defining file is relative to the specified paths
        :return: a pair of (module name, type name) if successful, where module_name is None is the type is a builtin
        """
        # 0. builtin types
        module = sys.modules[ty.__module__]
        logger.debug(f"{(module.__name__, ty.__name__)} as builtin?")
        if module.__name__ == "builtins":
            return None, ty.__qualname__

        # Special case:
        # The __file__ attribute is not present for C modules that are statically linked into the interpreter;
        # for extension modules loaded dynamically from a shared library,
        # it is the pathname of the shared library file.
        if not hasattr(module, "__file__"):
            return module.__name__, ty.__qualname__

        assert module.__file__ is not None
        module_file = pathlib.Path(module.__file__)

        # 1. project path
        if module_file.is_relative_to(self.proj_path):
            logger.debug(
                f"{(module.__name__, ty.__qualname__)} is relative to project path"
            )
            rel_path = module_file.relative_to(self.proj_path)

        # 2. stdlib
        elif module_file.is_relative_to(self.stdlib_path):
            logger.debug(f"{(module.__name__, ty.__qualname__)} is relative to stdlib path")
            rel_path = module_file.relative_to(self.stdlib_path)

        # 3. venv
        elif module_file.is_relative_to(self.site_packages):
            logger.debug(f"{(module.__name__, ty.__qualname__)} is a venv dependency")
            rel_path = module_file.relative_to(self.site_packages)

        else:
            logger.warning(
                f"Failed to lookup {ty} ({ty.__module__}) from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
            )
            return None

        relmod = str(rel_path.with_suffix("")).replace(os.path.sep, ".")
        return relmod, ty.__qualname__
