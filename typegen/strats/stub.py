import pathlib
import tempfile

from mypy import stubgen
import pandas as pd
import libcst as cst
from typegen.strats.gen import TypeHintGenerator

from typegen.strats.inline import TypeHintTransformer


class _ImportUnionTransformer(cst.CSTTransformer):
    def __init__(self):
        self.requires_union_import = False

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module):
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
        if not hasattr(node, "annotation") or node.annotation is None:
            return True
        self._check_annotation_union(node.annotation.annotation)
        return True

    def visit_FunctionDef_returns(self, node: cst.FunctionDef) -> None:
        if node.returns:
            self._check_annotation_union(node.returns.annotation)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        self._check_annotation_union(node.annotation.annotation)
        return True

    def _check_annotation_union(self, node: cst.CSTNode | None) -> None:
        if self.requires_union_import:
            return
        if isinstance(node, cst.Subscript):
            if isinstance(node.value, cst.Name) and node.value.value == "Union":
                self.requires_union_import = True


class StubFileGenerator(TypeHintGenerator):
    """Generates stub files using mypy.stubgen."""

    ident = "stub"

    def _transformers(self, module_path: str, applicable: pd.DataFrame) -> list[cst.CSTTransformer]:
        return [
            TypeHintTransformer(module_path, applicable)
        ]


    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Stub means generating a stub without overwriting the original
        root = pathlib.Path.cwd()

        # Store inline hinted ast in temporary file so that mypy can 
        # extract our applied hints to it
        with tempfile.NamedTemporaryFile() as temphinted:
            temp_py_file_path = pathlib.Path(temphinted.name)

            with temp_py_file_path.open("w") as f:
                f.write(hinting.code)

            # Generates the stub file by generating the file (temporary)
            # and use stubgen to generate a stub file from the generated file.
            options = stubgen.parse_options([str(temp_py_file_path)])
            mypy_opts = stubgen.mypy_options(options)

            module = stubgen.StubSource("temp", str(temp_py_file_path))

            stubgen.generate_asts_for_modules([module], False, mypy_opts, options.verbose)
            assert module.path is not None, "Not found module was not skipped"
            relative_stub_file_path = str(source_file.relative_to(root).with_suffix(".pyi"))

            with stubgen.generate_guarded(module.module, relative_stub_file_path):
                stubgen.generate_stub_from_ast(
                    module, relative_stub_file_path, False, options.pyversion
                )

            # Adds the missing "from typing import Union" statement.
            path_of_stub_file = root / relative_stub_file_path
            with path_of_stub_file.open() as file:
                stub_file_content = file.read()

            stub_cst = cst.parse_module(stub_file_content)

            transformer = _ImportUnionTransformer()
            stub_cst = stub_cst.visit(transformer)

            with path_of_stub_file.open("w") as f:
                f.write(stub_cst.code)
