import pathlib
import libcst as cst
from mypy import stubgen
import constants
from tracing.ptconfig import load_config
from typegen.strats.inline import InlineGenerator


def _get_temp_folder_path(root: pathlib.Path) -> pathlib.Path:
    cfg = load_config(root / constants.CONFIG_FILE_NAME)
    if cfg.pytypes.proj_path != root:
        raise RuntimeError(
            f"Invalid config file: wrong project root: Program has been executed in {root}, "
            f"but config file has {cfg.pytypes.proj_path} set"
        )

    return root / StubFileGenerator.RELATIVE_TEMP_FOLDER_PATH


def validate_temp_file_path(temp_file_path: pathlib.Path) -> None:
    if temp_file_path.exists():
        assert temp_file_path.is_file()
        assert temp_file_path.stat().st_size == 0, f"{temp_file_path} is not empty!"


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
            new_body = [typings_line] + list(updated_node.body)

            return updated_node.with_changes(body=new_body)
        return updated_node

    def visit_Param(self, node: cst.Param) -> bool | None:
        if not hasattr(node, "annotation") or node.annotation is None:
            return True
        self._check_annotation_union(node.annotation.annotation)
        return True

    def visit_FunctionDef_returns(self, node: cst.FunctionDef) -> bool | None:
        if node.returns:
            self._check_annotation_union(node.returns.annotation)
        return True

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        self._check_annotation_union(node.annotation.annotation)

    def _check_annotation_union(self, node: cst.CSTNode | None) -> None:
        if self.requires_union_import:
            return
        if isinstance(node, cst.Subscript):
            if isinstance(node.value, cst.Name) and node.value.value == "Union":
                self.requires_union_import = True


class StubFileGenerator(InlineGenerator):
    """Generates stub files using mypy.stubgen."""

    RELATIVE_TEMP_FOLDER_PATH = pathlib.Path("pytypes") / "typegen" / "stub" / "temp"
    TEMP_PY_FILENAME = "temp.py"
    TEMP_STUB_FILENAME = "temp.pyi"
    ident = "stub"

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Stub means generating a stub without overwriting the original
        root = pathlib.Path.cwd()

        temp_folder_path = _get_temp_folder_path(root)
        temp_folder_path.mkdir(parents=True, exist_ok=True)

        temp_py_file_path = temp_folder_path / StubFileGenerator.TEMP_PY_FILENAME

        validate_temp_file_path(temp_py_file_path)

        super()._store_hinted_ast(temp_py_file_path, hinting)

        # Generates the stub file by generating the file (temporary)
        # and use stubgen to generate a stub file from the generated file.
        options = stubgen.parse_options([str(temp_py_file_path)])
        mypy_opts = stubgen.mypy_options(options)

        module = stubgen.StubSource("temp", str(temp_py_file_path))

        stubgen.generate_asts_for_modules([module], False, mypy_opts, options.verbose)
        assert module.path is not None, "Not found module was not skipped"
        relative_stub_file_path = str(source_file.relative_to(root).with_suffix(".pyi"))

        try:
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

            super()._store_hinted_ast(path_of_stub_file, stub_cst)
        finally:
            # Clears the file content.
            temp_py_file_path.open("w").close()
