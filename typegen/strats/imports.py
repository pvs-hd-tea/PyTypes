import grp
import operator
import functools
import os

import libcst as cst
import pandas as pd

from constants import TraceData


class _AddImportTransformer(cst.CSTTransformer):
    def __init__(self, applicable: pd.DataFrame) -> None:
        self.applicable = applicable.copy()

    # There is probably a better implementation using LibCST's AddImportVisitor and CodemodContext
    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        def file2module(file: str) -> str:
            return os.path.splitext(file.replace(os.path.sep, "."))[0]

        # Stupid implementation: make from x import y everywhere
        self.applicable["modules"] = self.applicable[TraceData.FILENAME].map(
            lambda f: file2module(f)
        )

        # ignore builtins
        non_builtin = self.applicable[TraceData.VARTYPE_MODULE].notnull()
        # ignore classes in the same module
        not_in_same_mod = (
            self.applicable["modules"] != self.applicable[TraceData.VARTYPE_MODULE]
        )
        retain_mask = [
            non_builtin,
            not_in_same_mod,
        ]

        important = self.applicable[functools.reduce(operator.and_, retain_mask)]
        if important.empty:
            return updated_node

        assert not important.duplicated().any()
        importables = important.groupby(
            by=[TraceData.VARTYPE_MODULE, TraceData.VARTYPE],
            sort=False,
            dropna=False
        )

        imports_for_type_hints = []
        for _, group in importables:
            modules = group[TraceData.VARTYPE_MODULE].values[0]
            types = group[TraceData.VARTYPE].values[0]
            
            modules = modules.split(",")
            types = types.split(" | ")

            for module, ty in zip(modules, types):
                if not module:
                    continue

                mod_name = cst.parse_expression(module)
                assert isinstance(
                    mod_name, cst.Name | cst.Attribute
                ), f"Accidentally parsed {type(mod_name)}"

                aliases = [cst.ImportAlias(name=cst.Name(ty))]
                imp_from = cst.ImportFrom(module=mod_name, names=aliases)
                imports_for_type_hints.append(cst.SimpleStatementLine([imp_from]))

        typings_import = cst.ImportFrom(
            module=cst.Name(value="typing"),
            names=[cst.ImportAlias(cst.Name("TYPE_CHECKING"))],
        )
        typings_line = cst.SimpleStatementLine([typings_import])

        ann_fut_import = cst.ImportFrom(
            module=cst.Name(value="__future__"),
            names=[cst.ImportAlias(cst.Name("annotations"))],
        )
        ann_fut_line = cst.SimpleStatementLine([ann_fut_import])

        type_checking_only = cst.If(
            test=cst.Name("TYPE_CHECKING"),
            body=cst.IndentedBlock(imports_for_type_hints),
        )

        # mypy doesnt like us writing in NewLines into their body, but the codegen is fine
        new_body = [
            ann_fut_line,
            typings_line,
            type_checking_only,
        ] + list(updated_node.body)
        return updated_node.with_changes(body=new_body)
