import pathlib
import tempfile

from mypy import stubgen
import pandas as pd
import libcst as cst
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.imports import AddImportTransformer

from typegen.strats.inline import TypeHintTransformer


class ImportUnionTransformer(cst.CSTTransformer):
    """Transforms the CST by adding the ImportFrom node (from typing import Union) if the corresponding code contains a union type hint."""
    def __init__(self):
        """Creates an instance of ImportUnionTransformer."""
        self.requires_union_import = False

    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Adds the ImportFrom node to the CST if a union type hint has been found.
        :param updated_node: The updated node.
        :returns: The updated node with the added ImportFrom node if a union type hint has been found, otherwise the updated node without any changes.
        
        """
        if self.requires_union_import:
            typing_union_import = cst.ImportFrom(
                module=cst.Name(value="typing"),
                names=[cst.ImportAlias(cst.Name("Union"))],
            )

            typings_line = cst.SimpleStatementLine([typing_union_import])
            new_body = [typings_line] + list(updated_node.body)  # type: ignore
            # Note: Same code as in typegen/strats/imports.py

            return updated_node.with_changes(body=new_body)
        return updated_node

    def visit_Param(self, node: cst.Param) -> bool | None:
        """Checks whether the parameter node contains a union type hint.
        :param node: The visited node."""
        if not hasattr(node, "annotation") or node.annotation is None:
            return True
        self._check_annotation_union(node.annotation.annotation)
        return True

    def visit_FunctionDef_returns(self, node: cst.FunctionDef) -> None:
        """Checks whether the function def node contains a union type hint for the return type.
        :param node: The visited node."""
        if node.returns:
            self._check_annotation_union(node.returns.annotation)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        """Checks whether the annotated assignment node contains a union type hint.
        :param node: The visited node."""
        self._check_annotation_union(node.annotation.annotation)
        return True

    def _check_annotation_union(self, node: cst.CSTNode | None) -> None:
        if self.requires_union_import:
            return
        if isinstance(node, cst.Subscript):
            if isinstance(node.value, cst.Name) and node.value.value == "Union":
                self.requires_union_import = True


class MyPyHintTransformer(cst.CSTTransformer):
    """Replaces the CST with the corresponding stub CST, generated using mypy.stubgen."""
    def leave_Module(
        self, _: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Replaces the CST with the corresponding stub CST, generated using mypy.stubgen.
        :param updated_node: The updated node.
        :returns: The stub CST.
        
        """
        # Store inline hinted ast in temporary file so that mypy can
        # extract our applied hints to it
        with tempfile.NamedTemporaryFile() as temphinted, tempfile.NamedTemporaryFile() as tempstub:
            temp_py_file_path = pathlib.Path(temphinted.name)
            tempstub_path = pathlib.Path(tempstub.name)

            with temp_py_file_path.open("w") as f:
                f.write(updated_node.code)

            # Generates the stub file by generating the file (temporary)
            # and use stubgen to generate a stub file from the generated file.
            options = stubgen.parse_options([temphinted.name])
            mypy_opts = stubgen.mypy_options(options)

            module = stubgen.StubSource("temp", temphinted.name)

            stubgen.generate_asts_for_modules(
                py_modules=[module],
                parse_only=False,
                mypy_options=mypy_opts,
                verbose=options.verbose,
            )
            with stubgen.generate_guarded(module.module, tempstub_path.name):
                stubgen.generate_stub_from_ast(
                    mod=module,
                    target=tempstub.name,
                    parse_only=False,
                    pyversion=options.pyversion,
                )

            with tempstub_path.open() as file:
                stub_file_content = file.read()

            return cst.parse_module(stub_file_content)


class StubFileGenerator(TypeHintGenerator):
    """Generates stub files using mypy.stubgen."""

    ident = "stub"

    def _transformers(
        self, module_path: str, applicable: pd.DataFrame
    ) -> list[cst.CSTTransformer]:
        return [
            TypeHintTransformer(module_path, applicable),
            AddImportTransformer(applicable),
            MyPyHintTransformer(),
            ImportUnionTransformer(),
        ]

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        with source_file.with_suffix(".pyi").open("w") as f:
            f.write(hinting.code)
