import abc
import logging
import os
import pathlib
import typing

import libcst as cst
import pandas as pd

from constants import Column

logger = logging.getLogger(__name__)


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

    def apply(self, root: pathlib.Path):
        """Applies the type hint generation on the files in the root folder.
        
        :param root: The root folder path."""
        files = self.types[Column.FILENAME].unique()
        as_paths = map(pathlib.Path, files)
        for path in filter(self._is_hintable_file, as_paths):
            # Get type hints relevant to this file
            applicable = self.types[self.types[Column.FILENAME] == str(path)]
            if not applicable.empty:
                logger.info(f"Generating type hints for {path}")

                from_root = root / path
                module = cst.parse_module(source=from_root.open().read())

                typed = self._gen_hinted_ast(applicable=applicable, module=module)
                self._store_hinted_ast(source_file=from_root, hinting=typed)

    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, module: cst.Module
    ) -> cst.Module:
        """
        Perform operations to generate types for the given file
        """
        filename = applicable[Column.FILENAME].values[0]
        assert filename is not None

        path = os.path.splitext(filename)[0]
        as_module = path.replace(os.path.sep, ".")

        applied = module
        for transformer in self._transformers(as_module, applicable):
            if hasattr(transformer, "METADATA_DEPENDENCIES"):
                applied = cst.MetadataWrapper(applied).visit(transformer)
            else:
                applied = applied.visit(transformer)

        return applied

    @abc.abstractmethod
    def _transformers(
        self, module_path: str, applicable: pd.DataFrame
    ) -> list[cst.CSTTransformer]:
        pass

    @abc.abstractmethod
    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        """
        Store the hinted AST at the correct location, based upon the `source_file` param
        """
        pass