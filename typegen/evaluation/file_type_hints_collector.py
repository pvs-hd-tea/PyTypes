import os.path
import pathlib
from typing import Dict

import pandas as pd
import libcst as cst
from libcst.metadata import PositionProvider

import constants
from tracing import TraceDataCategory


class FileTypeHintsCollector:
    """Collects the type hints of multiple .py files."""
    def __init__(self, project_dir: pathlib.Path):
        self.project_dir = project_dir
        self.typehint_data = pd.DataFrame()
        self.file_path = ""

    def collect_data(self, file_paths: list[pathlib.Path]) -> None:
        """Collects the type hints of the provided file paths."""
        for file_path in file_paths:
            with file_path.open() as file:
                file_content = file.read()

            module = cst.parse_module(source=file_content)
            module_and_meta = cst.MetadataWrapper(module)
            relative_path = str(pathlib.Path(os.path.relpath(file_path.resolve(), self.project_dir.resolve())))
            visitor = TypeHintVisitor(relative_path)
            module_and_meta.visit(visitor)
            typehint_data = visitor.typehint_data.astype(constants.TraceData.TYPE_HINT_SCHEMA)

            self.typehint_data = pd.concat(
                [self.typehint_data, typehint_data], ignore_index=True
            ).astype(constants.TraceData.TYPE_HINT_SCHEMA)


class TypeHintVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path
        self.typehint_data = pd.DataFrame(columns=constants.TraceData.TYPE_HINT_SCHEMA.keys())
        self._scope_stack: list[cst.FunctionDef | cst.ClassDef] = []
        self.imports: Dict[str, str] = {}

    def _innermost_class(self) -> cst.ClassDef | None:
        fromtop = reversed(self._scope_stack)
        classes = filter(lambda p: isinstance(p, cst.ClassDef), fromtop)

        first: cst.ClassDef | None = next(classes, None)  # type: ignore
        return first

    def _innermost_function(self) -> cst.FunctionDef | None:
        fromtop = reversed(self._scope_stack)
        fdefs = filter(lambda p: isinstance(p, cst.FunctionDef), fromtop)

        first: cst.FunctionDef | None = next(fdefs, None)  # type: ignore
        return first

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        module_name: str = str(node.module.value)  # type: ignore
        for name in node.names:  # type: ignore
            class_name: str = str(name.name.value)
            self.imports[class_name] = module_name
        return True

    def visit_ClassDef(self, cdef: cst.ClassDef) -> bool | None:
        # Track ClassDefs to disambiguate functions from methods
        self._scope_stack.append(cdef)
        return True

    def leave_ClassDef(self, _: cst.ClassDef) -> None:
        self._scope_stack.pop()

    def visit_FunctionDef(self, fdef: cst.FunctionDef) -> bool | None:
        # Track assignments from Functions
        # NOTE: this handles nested functions too, because the parent reference gets overwritten
        # NOTE: before we start generating hints for its children
        self._scope_stack.append(fdef)
        return True

    def leave_FunctionDef(self, fdef: cst.FunctionDef) -> None:
        self._scope_stack.pop()

    def visit_Param(self, node: cst.Param) -> bool | None:
        if not hasattr(node, "annotation"):
            return True
        variable_name, line_number = self._get_name_and_line_number(node)
        type_hint = self._get_annotation_value(node.annotation)
        self._add_row(line_number, TraceDataCategory.FUNCTION_PARAMETER, variable_name, type_hint)
        return True

    def visit_FunctionDef_returns(self, node: cst.FunctionDef) -> None:
        variable_name, line_number = self._get_name_and_line_number(node)
        if node.returns:
            type_hint = self._get_annotation_value(node.returns)
        else:
            type_hint = None
        self._add_row(line_number, TraceDataCategory.FUNCTION_RETURN, variable_name, type_hint)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        if not hasattr(node, "annotation"):
            return True
        _, line_number = self._get_name_and_line_number(node)

        type_hint = self._get_annotation_value(node.annotation)
        if isinstance(node.target, cst.Attribute):
            category = TraceDataCategory.CLASS_MEMBER
            variable_name = node.target.attr.value
        elif isinstance(node.target, cst.Name):
            category = TraceDataCategory.LOCAL_VARIABLE
            variable_name = node.target.value
        else:
            raise TypeError("Unhandled case for: " + type(node.annotation.annotation).__name__)
        self._add_row(line_number, category, variable_name, type_hint)
        return True

    def _get_name_and_line_number(self, node):
        pos = self.get_metadata(PositionProvider, node).start
        variable_name = None if not hasattr(node, "name") else node.name.value
        variable_line_number = pos.line
        return variable_name, variable_line_number

    def _add_row(self, line_number: int, category: TraceDataCategory, variable_name: str | None, type_hint: str | None):
        class_node = self._innermost_class()
        class_name = None
        if class_node:
            class_name = class_node.name.value
        function_node = self._innermost_class()
        function_name = None
        if function_node:
            function_name = function_node.name.value
        self.typehint_data.loc[len(self.typehint_data.index)] = [
            self.file_path,
            class_name,
            function_name,
            line_number,
            category,
            variable_name,
            type_hint,
        ]

    def _get_annotation_value(self, annotation: cst.Annotation | None) -> str | None:
        if annotation is None:
            return None

        actual_annotation = annotation.annotation
        if isinstance(actual_annotation, cst.Attribute):
            module_name = actual_annotation.value.value  # type: ignore
            type_name = actual_annotation.attr.value
            return module_name + "." + type_name
        elif isinstance(actual_annotation, cst.Name):
            type_name = actual_annotation.value
            if type_name in self.imports.keys():
                module_name = self.imports[type_name]
                return module_name + "." + type_name
            return type_name
        else:
            raise TypeError("Unhandled case for: " + type(actual_annotation).__name__)
