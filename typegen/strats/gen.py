import abc
import pathlib
import typing

import libcst as cst
from libcst.metadata.position_provider import PositionProvider
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
                module = cst.parse_module(source=path.open().read())
                module_and_meta = cst.MetadataWrapper(module)

                typed = self._gen_hinted_ast(df=applicable, hintless_ast=module_and_meta)
                self._store_hinted_ast(source_file=path, hinting=typed)

    @abc.abstractmethod
    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, hintless_ast: cst.MetadataWrapper
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
