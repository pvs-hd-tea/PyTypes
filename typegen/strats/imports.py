import operator
import functools
import os

import libcst as cst
from libcst import matchers as m
import pandas as pd
import logging
from constants import Column


logger = logging.getLogger(__name__)


class AddImportTransformer(cst.CSTTransformer):
    """Transforms the CST by adding ImportFrom nodes to import the modules of 
    the type hints according to the trace data."""
    _FUTURE_IMPORT_MATCH = m.ImportFrom(module=m.Name(value="__future__"))
    _ANNOTATION_MATCH = m.ImportAlias(name=m.Name(value="annotations"))

    def __init__(self, applicable: pd.DataFrame) -> None:
        self.applicable = applicable.copy()
        self._future_imports: set[cst.ImportAlias] = set()
        self._contains_anno_fut_import: bool = False

    def leave_ImportFrom(
        self, _: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom | cst.RemovalSentinel:
        # Interestingly, star imports in __future__ are not possible
        # >>> from __future__ import *
        # File "<stdin>", line 1
        # SyntaxError: future feature * is not defined
        # So no ImportStar can occur here
        if m.matches(updated_node, AddImportTransformer._FUTURE_IMPORT_MATCH):
            if any(
                m.matches(alias, AddImportTransformer._ANNOTATION_MATCH)
                for alias in updated_node.names   # type: ignore
            ):
                self._contains_anno_fut_import = True

            self._future_imports.update(set(updated_node.names))  # type: ignore
            return cst.RemoveFromParent()

        return updated_node

    # There is probably a better implementation using LibCST's AddImportVisitor and CodemodContext
    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        def file2module(file: str) -> str:
            return os.path.splitext(file.replace(os.path.sep, "."))[0]

        # Stupid implementation: make from x import y everywhere
        self.applicable["modules"] = self.applicable[Column.FILENAME].map(
            lambda f: file2module(f)
        )

        # ignore builtins
        non_builtin = self.applicable[Column.VARTYPE_MODULE].notnull()
        # ignore classes in the same module
        not_in_same_mod = (
            self.applicable["modules"] != self.applicable[Column.VARTYPE_MODULE]
        )
        retain_mask = [non_builtin, not_in_same_mod]

        important = self.applicable[functools.reduce(operator.and_, retain_mask)]
        if important.empty:
            return updated_node

        assert not important.duplicated().any()
        importables = important.groupby(
            by=[Column.VARTYPE_MODULE, Column.VARTYPE], sort=False, dropna=False
        )

        imports_for_type_hints = []
        for _, group in importables:
            modules = group[Column.VARTYPE_MODULE].values[0]
            types = group[Column.VARTYPE].values[0]

            modules = modules.split(",")
            types = types.split(" | ")

            for module, ty in zip(modules, types):
                if not module:
                    continue

                mod_name = cst.parse_expression(module)

                if not isinstance(
                        mod_name, cst.Name | cst.Attribute
                    ):
                    logger.warning(f"{group[Column.FILENAME].values[0]}: Accidentally parsed {type(mod_name)} | {module} | {ty}")
                    continue
                # For inner types, the outermost attr exposes them
                outer_most = ty.split(".")[0]
                aliases = [cst.ImportAlias(name=cst.Name(outer_most))]
                imp_from = cst.ImportFrom(module=mod_name, names=aliases)
                imports_for_type_hints.append(cst.SimpleStatementLine([imp_from]))

        typings_import = cst.ImportFrom(
            module=cst.Name(value="typing"),
            names=[cst.ImportAlias(cst.Name("TYPE_CHECKING"))],
        )
        typings_line = cst.SimpleStatementLine([typings_import])

        if not self._contains_anno_fut_import:
            self._future_imports.add(cst.ImportAlias(cst.Name("annotations")))

        fut_imports = cst.ImportFrom(
            module=cst.Name(value="__future__"),
            names=list(self._future_imports),
        )

        fut_import_line = cst.SimpleStatementLine([fut_imports])

        type_checking_only = cst.If(
            test=cst.Name("TYPE_CHECKING"),
            body=cst.IndentedBlock(imports_for_type_hints),
        )

        # mypy doesnt like us writing in NewLines into their body, but the codegen is fine
        new_body = [
            fut_import_line,
            typings_line,
            type_checking_only,
        ] + list(updated_node.body)
        return updated_node.with_changes(body=new_body)
