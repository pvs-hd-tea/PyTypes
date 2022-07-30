import abc, ast
import pathlib
import typing

import pandas as pd

import constants


class TypeHintGenerator(abc.ABC):
    """Base class for different generation styles of type hints"""

    _REGISTRY: dict[str, typing.Type["TypeHintGenerator"]] = {}
    _PATH_GLOB = "*.py"

    types: pd.DataFrame

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        TypeHintGenerator._REGISTRY[cls.ident] = cls

    def __new__(
        cls: typing.Type["TypeHintGenerator"], /, ident: str, types: pd.DataFrame
    ) -> "TypeHintGenerator":
        if (subcls := TypeHintGenerator._REGISTRY.get(ident, None)) is not None:
            subinst = object.__new__(subcls)
            subinst.types = types

            return subinst

        raise LookupError(f"Unsupported typegen strategy format: {ident}")

    def _is_hintable_file(self, path: pathlib.Path) -> bool:
        if path.name.endswith("__init__.py"):
            return False

        return True

    def apply(self):
        files = self.types[constants.TraceData.FILENAME].unique()
        for path in filter(self._is_hintable_file, files):
            # Get type hints relevant to this file
            applicable = self.types[
                self.types[constants.TraceData.FILENAME] == str(path)
            ]
            if not applicable.empty:
                nodes = ast.parse(source=path.open().read(), type_comments=True)
                typed = self._gen_hints(df=applicable, nodes=nodes)
                self._store_hints(source_file=path, hinting=typed)

    @abc.abstractmethod
    def _gen_hints(self, applicable: pd.DataFrame, nodes: ast.AST) -> ast.AST:
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
