import ast
import functools
import logging
import operator
import pathlib
import itertools

from constants import TraceData
from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator

import pandas as pd

logger = logging.getLogger(__name__)


class TypeHintTransformer(ast.NodeTransformer):
    def __init__(self, relevant: pd.DataFrame) -> None:
        super().__init__()
        self.df = relevant

    def generic_visit(self, node: ast.AST) -> ast.AST:
        # Track ClassDefs and FunctionDefs to disambiguate
        # functions from methods
        if isinstance(node, ast.ClassDef):
            for child in filter(lambda c: isinstance(c, ast.FunctionDef), node.body):
                child.parent = node  # type: ignore

        # Track assignments from Functions
        # NOTE: this handles nested functions too, because the parent reference gets overwritten
        # NOTE: before we start generating hints for its children
        if isinstance(node, ast.FunctionDef):
            for direct in ast.iter_child_nodes(node):
                for child in ast.walk(direct):  # type: ignore
                    child.parent = node  # type: ignore

        return super().generic_visit(node)

    def visit_FunctionDef(self, fdef: ast.FunctionDef):
        logger.debug(f"Applying hints to '{fdef.name}'")

        self._add_parameter_hints(fdef)
        self._add_return_hint(fdef)

        self.generic_visit(fdef)
        return fdef

    def _add_parameter_hints(self, fdef: ast.FunctionDef) -> None:
        # parameters
        param_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_ARGUMENT,
            self.df[TraceData.FUNCNAME] == fdef.name,
        ]
        params = self.df[functools.reduce(operator.and_, param_masks)]

        # NOTE: disregards *args (fdef.vararg) and **kwargs (fdef.kwarg)
        for arg in itertools.chain(fdef.args.posonlyargs, fdef.args.args):
            # Narrow by line number and identifier
            arg_hint_mask = [
                params[TraceData.LINENO] == arg.lineno,
                params[TraceData.VARNAME] == arg.arg,
            ]
            arg_hints = params[functools.reduce(operator.and_, arg_hint_mask)]
            assert (
                arg_hints.shape[0] <= 1
            ), f"Found multiple hints for the parameter type: {arg_hints}"

            # no type hint, skip
            if arg_hints.shape[0] == 0:
                logger.debug(f"No hint found for '{arg.arg}'")
                continue

            argtype = arg_hints[TraceData.VARTYPE].values[0]
            assert argtype is not None

            arg_hint = argtype.__name__
            logger.debug(f"Applying hint '{arg_hint}' to '{arg.arg}'")
            arg.annotation = ast.Name(arg_hint)

    def _add_return_hint(self, fdef: ast.FunctionDef) -> None:
        # disambiguate methods from functions
        clazz_name = self._find_class(fdef)

        if clazz_name is not None:
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            clazz_mask = names == clazz_name
        else:
            clazz_mask = self.df[TraceData.CLASS].isnull()

        rettype_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
            clazz_mask,
            self.df[TraceData.VARNAME] == fdef.name,
            self.df[TraceData.LINENO] == 0,  # return type, always stored at line 0
        ]
        rettypes = self.df[functools.reduce(operator.and_, rettype_masks)]

        assert (
            rettypes.shape[0] <= 1
        ), f"Found multiple hints for the return type:\n{rettypes[TraceData.VARTYPE].values}"

        # no type hint, skip
        if rettypes.shape[0] == 0:
            logger.debug(f"No hint found for return for '{fdef.name}'")

        if rettypes.shape[0] == 1:
            rettype = rettypes[TraceData.VARTYPE].values[0]
            assert rettype is not None

            ret_hint = rettype.__name__
            logger.debug(f"Applying return type hint '{ret_hint}' to '{fdef.name}'")
            fdef.returns = ast.Name(ret_hint)

    def _find_class(self, node: ast.AST) -> str | None:
        class_name = None
        while hasattr(node, "parent"):
            node = node.parent  # type: ignore
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                break

        return class_name

    def _find_targets(self, node: ast.Assign | ast.AnnAssign | ast.AugAssign):
        if isinstance(node, ast.AnnAssign | ast.AugAssign):
            target = node.target
            return self._extract_target_names_with_nodes(target)
        else:
            targets = node.targets
            names = list()
            for target in targets:
                names += self._extract_target_names_with_nodes(target)
            return names

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST | list[ast.AST]:
        replace = self._visit_assigns(node)
        assert isinstance(replace, list)

        return replace

    def visit_Assign(self, node: ast.Assign) -> ast.AST | list[ast.AST]:
        return self._visit_assigns(node)

    def _visit_assigns(
        self, node: ast.Assign | ast.AugAssign
    ) -> ast.AST | list[ast.AST]:
        if not node.value:
            return node

        target_names_with_nodes = self._find_targets(node)
        target_names = [
            target_name_with_node[0]
            for target_name_with_node in target_names_with_nodes
        ]

        logger.debug(f"Applying hints to '{target_names}'")

        class_name = self._find_class(node)
        if class_name is not None:
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            class_check = names == class_name
        else:
            class_check = self.df[TraceData.CLASS].isnull()

        var_mask_local_variables = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[TraceData.VARNAME].isin(target_names),
            self.df[TraceData.LINENO] == node.lineno,
            class_check,
        ]

        var_mask_class_members = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[TraceData.VARNAME].isin(target_names),
            class_check,
        ]

        local_traced_vars = self.df[
            functools.reduce(operator.and_, var_mask_local_variables)
        ]
        class_members = self.df[functools.reduce(operator.and_, var_mask_class_members)]

        # Attach hint directly to assignment and promote to AnnAssign
        new_nodes: list[ast.AST] = []
        contains_one_target = len(target_names_with_nodes) == 1
        for target_name_with_node in target_names_with_nodes:
            target_name = target_name_with_node[0]
            target_node = target_name_with_node[1]
            target_trace_data = None
            if isinstance(target_node, ast.Attribute):
                # Finds the class member type hint.
                target_trace_data = class_members[
                    class_members[TraceData.VARNAME] == target_name
                ]
            elif isinstance(target_node, ast.Name):
                # Finds the local variable type hint.
                target_trace_data = local_traced_vars[
                    local_traced_vars[TraceData.VARNAME] == target_name
                ]
            if target_trace_data is None or len(target_trace_data) == 0:
                logger.debug(f"No hint found for assign for '{target_name}'")
                continue

            logger.debug(f"Applying type hints for simple assignment '{target_name}'")
            ann = target_trace_data[TraceData.VARTYPE].values[0].__name__

            if contains_one_target and not isinstance(node, ast.AugAssign):
                new_node = ast.AnnAssign(
                    target_node,
                    value=node.value,
                    annotation=ast.Name(ann),
                    simple=True,
                )
                return new_node
            else:
                new_node = ast.AnnAssign(
                    target_node,
                    annotation=ast.Name(ann),
                    simple=True,
                )
                new_nodes.append(new_node)

        new_nodes.append(node)
        return new_nodes

    def _extract_target_names_with_nodes(
        self, node: ast.AST
    ) -> list[tuple[str, ast.Name | ast.Attribute]]:
        """Returns the target names with the corresponding nodes which have to be annotated."""

        # If the node is a target node which has to be annotated, the children of the node are not checked.
        # Otherwise, it will recursively check the children.
        # In the case of class members, this prevents the corresponding object node
        # to be considered as a node to be annotated.
        target_names_with_nodes: list[tuple[str, ast.Name | ast.Attribute]] = []
        if isinstance(node, ast.Attribute):
            target_names_with_nodes.append((node.attr, node))
        elif isinstance(node, ast.Name):
            target_names_with_nodes.append((node.id, node))
        else:
            for child_node in ast.iter_child_nodes(node):
                target_names_with_nodes_in_child_node = (
                    self._extract_target_names_with_nodes(child_node)
                )
                target_names_with_nodes += target_names_with_nodes_in_child_node
        return target_names_with_nodes


class InlineGenerator(TypeHintGenerator):
    ident = "inline"

    def _gen_hinted_ast(self, applicable: pd.DataFrame, nodes: ast.AST) -> ast.AST:
        visitor = TypeHintTransformer(applicable)
        visitor.visit(nodes)

        return nodes

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: ast.AST) -> None:
        # Inline means overwriting the original
        contents = ast.unparse(hinting)
        with source_file.open("w") as f:
            f.write(contents)
