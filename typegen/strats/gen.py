import abc
import pathlib
import typing

import libcst as cst
import pandas as pd

from constants import TraceData
from .imports import _AddImportTransformer


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
        files = self.types[TraceData.FILENAME].unique()
        for path in filter(self._is_hintable_file, files):
            # Get type hints relevant to this file
            applicable = self.types[self.types[TraceData.FILENAME] == str(path)]
            if not applicable.empty:
                module = cst.parse_module(source=path.open().read())
                module_and_meta = cst.MetadataWrapper(module)

                typed = self._gen_hinted_ast(
                    df=applicable, ast_with_metadata=module_and_meta
                )
                imported = self._add_all_imports(applicable, typed)
                self._store_hinted_ast(source_file=path, hinting=imported)

    @abc.abstractmethod
    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, ast_with_metadata: cst.MetadataWrapper
    ) -> cst.Module:
        """
        Perform operations to generate types for the given file
        """
        pass

    @abc.abstractmethod
    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        """
        Store the hinted AST at the correct location, based upon the `source_file` param
        """
        pass

    def _add_all_imports(
        self,
        applicable: pd.DataFrame,
        hinted_ast: cst.Module,
    ) -> cst.Module:
        return hinted_ast.visit(_AddImportTransformer(applicable))
