import pathlib
from typing import Iterable
import pandas as pd
import libcst as cst
from libcst.metadata import PositionProvider
from tracing import TraceDataCategory
from typegen.evaluation.normalize_types import normalize_type

from constants import Column, Schema


class FileTypeHintsCollector:
    """Collects the type hints of multiple .py files."""

    typehint_data: pd.DataFrame

    def __init__(self):
        self.typehint_data = pd.DataFrame(columns=Schema.TypeHintData.keys())

    def collect_data_from_file(self, root: pathlib.Path, filename: str) -> None:
        self.collect_data_from_files(root, [filename])

    def collect_data_from_files(self, root: pathlib.Path, filenames: list[str]) -> None:
        file_paths = []
        for filename in filenames:
            file_path = (root / filename).resolve()
            assert file_path.is_file(), f"{file_path} is not a file path."
            file_paths.append(file_path)
        self.collect_data(root, file_paths)

    def collect_data_from_folder(
        self,
        root: pathlib.Path,
        folder: pathlib.Path,
        include_also_files_in_subdirectories: bool = False,
    ) -> None:
        assert folder.is_dir(), f"{folder} is not a folder path."
        file_pattern = "*.py"
        file_paths = (
            folder.rglob(file_pattern)
            if include_also_files_in_subdirectories
            else folder.glob(file_pattern)
        )
        # Ensures that the order is deterministic.
        sorted_file_paths = sorted(file_paths)
        self.collect_data(root, sorted_file_paths)

    def collect_data(
        self, root: pathlib.Path, file_paths: Iterable[pathlib.Path]
    ) -> None:
        self.typehint_data = self.typehint_data.iloc[0:0]
        """Collects the type hints of the provided file paths."""
        for file_path in file_paths:
            if not file_path.is_relative_to(root):
                raise ValueError(f"{file_path} is not relative to {root}")

            with file_path.open() as file:
                file_content = file.read()

            module = cst.parse_module(source=file_content)
            module_and_meta = cst.MetadataWrapper(module)
            relative_path_str = str(file_path.relative_to(root))
            visitor = _TypeHintVisitor(relative_path_str)
            module_and_meta.visit(visitor)
            typehint_data = visitor.typehint_data
            self.typehint_data = pd.concat(
                [self.typehint_data, typehint_data], ignore_index=True
            ).astype(Schema.TypeHintData)


class _TypeHintVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path
        self.typehint_data: pd.DataFrame = pd.DataFrame()
        self.collected_data: list = []
        self._scope_stack: list[cst.FunctionDef | cst.ClassDef] = []
        self.imports: dict[str, str] = {}
        self.imports_alias: dict[str, str] = {}
        self.smallest_column_offsets_by_line_number: dict[int, int] = {}
        self.defined_classes: list[str] = list()

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
        module_name = self._get_module_name(node)
        if not isinstance(node.names, cst.ImportStar):
            iterator = iter(node.names)
            for name in iterator:
                assert isinstance(name.name.value, str)
                imported_element_name: str = name.name.value
                if imported_element_name in self.imports.keys():
                    # The first import is considered as the module of the imported element.
                    continue
                self.imports[imported_element_name] = module_name
        return True

    def visit_Import(self, node: cst.Import) -> bool | None:
        try:
            iterator = iter(node.names)
            for name in iterator:
                if name.evaluated_alias is None:
                    continue
                module_name: str = name.evaluated_name
                module_alias: str = name.evaluated_alias
                self.imports_alias[module_alias] = module_name
        except TypeError:
            pass
        return True

    def visit_ClassDef(self, cdef: cst.ClassDef) -> bool | None:
        self.defined_classes.append(cdef.name.value)
        self._scope_stack.append(cdef)
        return True

    def leave_ClassDef(self, _: cst.ClassDef) -> None:
        self._scope_stack.pop()

    def visit_FunctionDef(self, fdef: cst.FunctionDef) -> bool | None:
        self._scope_stack.append(fdef)
        return True

    def leave_FunctionDef(self, fdef: cst.FunctionDef) -> None:
        self._scope_stack.pop()

    def visit_Param(self, node: cst.Param) -> bool | None:
        if not hasattr(node, "annotation") or node.annotation is None:
            return True
        variable_name = self._get_variable_name(node)
        type_hint = self._get_annotation_value(node.annotation.annotation)
        self._add_row(0, TraceDataCategory.FUNCTION_PARAMETER, variable_name, type_hint)
        return True

    def visit_FunctionDef_returns(self, node: cst.FunctionDef) -> None:
        variable_name = self._get_variable_name(node)
        if node.returns:
            type_hint = self._get_annotation_value(node.returns.annotation)
        else:
            type_hint = None
        self._add_row(0, TraceDataCategory.FUNCTION_RETURN, variable_name, type_hint)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        line_number = self._get_line_number(node)

        type_hint = self._get_annotation_value(node.annotation.annotation)
        if isinstance(node.target, cst.Attribute):
            category = TraceDataCategory.CLASS_MEMBER
            variable_name = node.target.attr.value
        elif isinstance(node.target, cst.Name):
            category = TraceDataCategory.LOCAL_VARIABLE
            variable_name = node.target.value
            if len(self._scope_stack) == 0:
                category = TraceDataCategory.GLOBAL_VARIABLE
                line_number = 0
        elif isinstance(node.target, cst.Subscript):
            # Example: a[0]: int = 1
            # These cases are not handled.
            return True
        else:
            raise TypeError(
                str(self.file_path)
                + ": Unhandled case for: "
                + type(node.target).__name__
            )
        self._add_row(line_number, category, variable_name, type_hint)
        return True

    def leave_Module(self, original_node: cst.Module) -> None:
        self.typehint_data = pd.DataFrame(
            self.collected_data, columns=Schema.TypeHintData.keys()
        )

        # The typehint data contains line numbers instead of column offsets. These are replaced with the column offset.
        self.typehint_data = self.typehint_data.replace(
            {Column.COLUMN_OFFSET: self.smallest_column_offsets_by_line_number}
        )

        self._unify_globals_in_data()


    def _get_variable_name(self, node: cst.FunctionDef | cst.Param) -> str:
        return node.name.value

    def _get_line_number(self, node: cst.CSTNode) -> int:
        pos = self.get_metadata(PositionProvider, node).start
        line_number = pos.line

        column_offset = pos.column
        if line_number in self.smallest_column_offsets_by_line_number.keys():
            self.smallest_column_offsets_by_line_number[line_number] = min(
                self.smallest_column_offsets_by_line_number[line_number], column_offset
            )
        else:
            self.smallest_column_offsets_by_line_number[line_number] = column_offset

        return line_number

    def _add_row(
        self,
        line_number: int,
        category: TraceDataCategory,
        variable_name: str | None,
        type_hint: str | None,
    ):
        class_node = self._innermost_class()
        class_name = None
        if class_node:
            class_name = class_node.name.value
        function_node = self._innermost_function()
        function_name = None
        if function_node:
            function_name = function_node.name.value
        if type_hint is not None:
            type_hint = normalize_type(type_hint)
        self.collected_data.append(
            [
                self.file_path,
                class_name,
                function_name,
                line_number,
                category,
                variable_name,
                type_hint,
            ]
        )

    def _get_annotation_value(self, annotation: cst.CSTNode) -> str | None:
        if annotation is None:
            return None
        if isinstance(annotation, cst.BinaryOperation):
            # It is a union using | .
            return self._get_annotation_value_of_binary_operation_union(annotation)
        elif isinstance(annotation, cst.Subscript):
            # It is a type with an inner type.
            return self._get_annotation_value_of_subscript(annotation)
        elif isinstance(annotation, cst.Attribute):
            return self._get_annotation_value_of_attribute(annotation)
        elif isinstance(annotation, cst.Name):
            return self._get_annotation_value_of_name(annotation)
        elif isinstance(annotation, cst.List):
            return self._get_annotation_value_of_list(annotation)
        elif isinstance(annotation, cst.Ellipsis):
            return "..."
        raise TypeError(
            str(self.file_path) + ": Unhandled case for: " + type(annotation).__name__
        )

    def _get_annotation_value_of_list(self, annotation: cst.List) -> str:
        inner_content = ""
        for i, list_element in enumerate(annotation.elements):
            full_list_element_name = self._get_annotation_value(list_element.value)
            assert isinstance(full_list_element_name, str)
            if i == 0:
                inner_content = full_list_element_name
            else:
                inner_content += ", " + full_list_element_name
        return "[" + inner_content + "]"

    def _get_annotation_value_of_name(self, annotation: cst.Name) -> str:
        type_name = annotation.value
        if type_name in self.defined_classes:
            # If an import imports a class but a class with the same name is defined in the file,
            # the class in the file is used.
            return type_name
        if type_name in self.imports.keys():
            module_name = self.imports[type_name]
            current_annotation = module_name + "." + type_name
        else:
            current_annotation = type_name
        return self._add_full_module_name_to_annotation(current_annotation)

    def _get_annotation_value_of_attribute(
        self, annotation: cst.Attribute, add_full_module_name: bool = True
    ) -> str:
        if isinstance(annotation.value, cst.Name):
            module_name = annotation.value.value
        elif isinstance(annotation.value, cst.Attribute):
            module_name = self._get_annotation_value_of_attribute(
                annotation.value, False
            )
        else:
            raise TypeError(
                str(self.file_path)
                + ": Unhandled case for: "
                + type(annotation.value).__name__
            )
        assert isinstance(annotation.attr, cst.Name)
        type_name = annotation.attr.value
        current_annotation = module_name + "." + type_name
        if not add_full_module_name:
            return current_annotation
        return self._add_full_module_name_to_annotation(current_annotation)

    def _get_annotation_value_of_binary_operation_union(
        self, annotation: cst.BinaryOperation
    ) -> str:
        types_in_union = []

        left_node = annotation.left
        full_type_name = self._get_annotation_value(left_node)
        assert full_type_name is not None
        types_in_union.append(full_type_name)

        right_node = annotation.right
        full_type_name = self._get_annotation_value(right_node)
        assert full_type_name is not None
        types_in_union.append(full_type_name)

        return " | ".join(types_in_union)

    def _get_annotation_value_of_subscript(
        self, actual_annotation: cst.Subscript
    ) -> str:
        outer_type_node = actual_annotation.value
        full_outer_type_name = self._get_annotation_value(outer_type_node)
        assert isinstance(full_outer_type_name, str)
        inner_type_nodes = actual_annotation.slice
        inner_value = None
        for inner_type_node in inner_type_nodes:
            assert isinstance(inner_type_node.slice, cst.Index)
            full_inner_type_name = self._get_annotation_value(
                inner_type_node.slice.value
            )
            assert isinstance(full_inner_type_name, str)
            if inner_value is None:
                inner_value = full_inner_type_name
            else:
                inner_value += ", " + full_inner_type_name
        assert isinstance(inner_value, str)
        return full_outer_type_name + "[" + inner_value + "]"

    def _add_full_module_name_to_annotation(self, current_annotation: str) -> str:
        if "." not in current_annotation:
            return current_annotation

        splits = current_annotation.split(".", 1)
        first_module_element = splits[0]
        remaining_annotation = splits[1]

        # If the first element is an alias, replaces it with the actual module name.
        if first_module_element in self.imports_alias.keys():
            first_module_element = self.imports_alias[first_module_element]

        # If the first element is imported from a module, adds the module name.
        elif first_module_element in self.imports.keys():
            module_name = self.imports[first_module_element]
            first_module_element = module_name + "." + first_module_element

        return first_module_element + "." + remaining_annotation

    def _get_module_name(self, import_from_node: cst.ImportFrom) -> str:
        module_node = import_from_node.module
        if isinstance(module_node, cst.Name):
            return module_node.value
        if isinstance(module_node, cst.Attribute):
            module_name = module_node.attr.value
            current_module_node = module_node.value
            while isinstance(current_module_node, cst.Attribute):
                module_name = current_module_node.attr.value + "." + module_name
                current_module_node = current_module_node.value
            assert isinstance(current_module_node, cst.Name)
            module_name = current_module_node.value + "." + module_name
            return module_name
        else:
            raise NotImplementedError(type(module_node))

    def _unify_globals_in_data(self) -> None:
        if self.typehint_data.shape[0] == 0:
            return
        grouped_data = self.typehint_data.groupby(
            by=[Column.CATEGORY, Column.VARNAME],
            dropna=False,
            sort=False,
        )

        data_with_unified_globals = pd.concat([self._update_group(group) for _, group in grouped_data]).reset_index(drop=True)
        self.typehint_data = pd.DataFrame(data_with_unified_globals, columns=list(Schema.TypeHintData.keys())).astype(Schema.TypeHintData)

    def _update_group(self, group):
        updated_group = group.copy()
        if (updated_group[Column.CATEGORY] == TraceDataCategory.GLOBAL_VARIABLE).all():
            types = updated_group[Column.VARTYPE].tolist()
            updated_group[Column.VARTYPE] = normalize_type(" | ".join(types))
            updated_group = updated_group.drop_duplicates()
        return updated_group
