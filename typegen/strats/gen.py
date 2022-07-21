import abc
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

    def __new__(cls: type["Generator"], /, types: pd.DataFrame) -> "Generator":
        if (subcls := Generator._REGISTRY.get(cls.ident, None)) is not None:
            return object.__new__(subcls, types=types)

        raise LookupError(f"Unsupported typegen strategy format: {cls.ident}")
        

    def apply(self, project: Project):
        assert project.source_dir is not None
        paths = project.source_dir.rglob(Generator._PATH_GLOB)

        for path in filter(self._is_hintable_file, paths):
            self._apply(path)

    def _is_hintable_file(self, path: pathlib.Path) -> bool:
        if path.name.endswith("__init__.py"):
            return False

        return True

    @abc.abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """
        Perform IO operation to generate types for the given file 
        according to the derived strategy
        """
        pass