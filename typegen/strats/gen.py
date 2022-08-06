import abc
import logging
import operator
import functools
import os
import pathlib
import typing

import libcst as cst
import pandas as pd

import constants

# There is probably a better implementation using LibCST's AddImportVisitor and CodemodContext
class _AddImportVisitor(cst.CSTTransformer):
    def __init__(self, applicable: pd.DataFrame) -> None:
        self.applicable = applicable.copy()

    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        def file2module(file: str) -> str:
            return os.path.splitext(file.replace(os.path.sep, "."))[0]

        # Stupid implementation: make from x import y everywhere
        self.applicable["modules"] = self.applicable[constants.TraceData.FILENAME].map(
            lambda f: file2module(f)
        )

        # ignore builtins
        non_builtin = self.applicable[constants.TraceData.VARTYPE_MODULE].notnull()
        # ignore classes in the same module
        not_in_same_mod = (
            self.applicable["modules"]
            != self.applicable[constants.TraceData.VARTYPE_MODULE]
        )
        retain_mask = [
            non_builtin,
            not_in_same_mod,
        ]

        important = self.applicable[functools.reduce(operator.and_, retain_mask)]
        if important.empty:
            return updated_node

        importables = important.groupby(
            [constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]
        ).agg({constants.TraceData.VARTYPE: list})

        imports: list[cst.ImportFrom | cst.Newline] = []

        for module in importables.index:

            mod_name = cst.parse_expression(module[0])
            assert isinstance(
                mod_name, cst.Name | cst.Attribute
            ), f"Accidentally parsed {type(mod_name)}"
            aliases: list[cst.ImportAlias] = []

            for ty in importables.loc[module].values[0]:
                aliases.append(cst.ImportAlias(name=cst.Name(ty)))

            imp_from = cst.ImportFrom(module=mod_name, names=aliases)
            imports.append(imp_from)
            imports.append(cst.Newline())

        return updated_node.with_changes(body=imports + list(updated_node.body))


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

                typed = self._gen_hinted_ast(
                    df=applicable, hintless_ast=module_and_meta
                )
                imported = self._add_all_imports(applicable, typed)
                self._store_hinted_ast(source_file=path, hinting=imported)

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

    def _add_all_imports(
        self,
        applicable: pd.DataFrame,
        hinted_ast: cst.Module,
    ) -> cst.Module:
        return hinted_ast.visit(_AddImportVisitor(applicable))
