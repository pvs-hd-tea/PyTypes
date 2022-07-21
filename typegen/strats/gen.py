import abc, ast
import pathlib
import typing

import pandas as pd

from fetching.projio import Project


class Generator(abc.ABC):
    """Base class for different generation styles of type hints"""

    _REGISTRY: dict[str, typing.Type["Generator"]] = {}
    _PATH_GLOB = "*.py"

    def __init__(self, types: pd.DataFrame) -> None:
        self.types = types

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Generator._REGISTRY[cls.ident] = cls

    def __new__(
        cls: typing.Type["Generator"], /, ident: str, types: pd.DataFrame
    ) -> "Generator":
        if (subcls := Generator._REGISTRY.get(ident, None)) is not None:
            return object.__new__(subcls, types=types)

        raise LookupError(f"Unsupported typegen strategy format: {ident}")

    def _is_hintable_file(self, path: pathlib.Path) -> bool:
        if path.name.endswith("__init__.py"):
            return False

        return True

    def apply(self, project: Project):
        assert project.source_dir is not None
        paths = project.source_dir.rglob(Generator._PATH_GLOB)

        for path in filter(self._is_hintable_file, paths):
            self._gen_hints(path)

    @abc.abstractmethod
    def _gen_hints(self, source_file: pathlib.Path) -> ast.AST:
        """
        Perform operations to generate types for the given file
        """
        pass

    @abc.abstractmethod
    def _store_hints(self, source_file: pathlib.Path, hinting: ast.AST) -> None:
        """
        Perform operations to generate types for the given file
        """
        pass
