from dataclasses import dataclass
import importlib
from importlib.machinery import SourceFileLoader
import logging
import os
import pathlib
import sys
from types import ModuleType

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
        logger.debug(f"Could not import {module_name} from {str(root / lookup_path)}")

    return None


@dataclass
class Resolver:
    stdlib_path: pathlib.Path
    proj_path: pathlib.Path
    venv_path: pathlib.Path

    def type_lookup(
        self, module_name: str | None | pd._libs.missing.NAType, type_name: str
    ) -> type | None:
        # Follow import order specified by sys.path

        # 0. builtin types
        if not isinstance(module_name, str):
            # __builtins__ is typed as Module by mypy, but is dict in the REPL?
            builtin_ty: type = __builtins__[type_name]  # type: ignore
            return builtin_ty

        else:
            # recreate filename
            lookup_path = pathlib.Path(module_name.replace(".", os.path.sep) + ".py")

            # 1. project path
            module = _attempt_module_lookup(module_name, self.proj_path, lookup_path)
            if module is None:
                # 2. stdlib
                module = _attempt_module_lookup(
                    module_name, self.stdlib_path, lookup_path
                )

            if module is None:
                # 3. venv
                major, minor = sys.version_info[:2]
                site_packages = (
                    self.venv_path / "lib" / f"python{major}.{minor}" / "site-packages"
                )
                module = _attempt_module_lookup(module_name, site_packages, lookup_path)

            if module is None:
                logger.warning(
                    f"Failed to import {module_name} from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
                )
                return None

            variable_type: type = getattr(module, type_name)
            return variable_type
