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
        if isinstance(node, ast.FunctionDef):
            for child in filter(
                    lambda c: isinstance(c, ast.AugAssign | ast.AnnAssign | ast.Assign),
                    node.body,
            ):
                child.parent = node  # type: ignore

        return super().generic_visit(node)

    def visit_FunctionDef(self, fdef: ast.FunctionDef):
        logger.debug(f"Applying hints to '{fdef.name}'")
        # NOTE: disregards *args (fdef.vararg) and **kwargs (fdef.kwarg)

        # parameters
        param_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_ARGUMENT,
            self.df[TraceData.FUNCNAME] == fdef.name,
        ]
        params = self.df[functools.reduce(operator.and_, param_masks)]

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

            arg_hint = arg_hints[TraceData.VARTYPE].values[0]
            logger.debug(f"Applying hint '{arg_hint}' to '{arg.arg}'")
            arg.annotation = ast.Name(arg_hint)

        # disambiguate methods from functions
        if hasattr(fdef, "parent"):
            rettype_masks = [
                self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
                self.df[TraceData.CLASS] == fdef.parent.name,  # type: ignore
                self.df[TraceData.VARNAME] == fdef.name,
                self.df[TraceData.LINENO] == 0,  # return type, always stored at line 0
            ]

        else:
            rettype_masks = [
                self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
                self.df[TraceData.CLASS].isnull(),
                self.df[TraceData.VARNAME] == fdef.name,
                self.df[TraceData.LINENO] == 0,
            ]

        rettypes = self.df[functools.reduce(operator.and_, rettype_masks)]

        assert (
                rettypes.shape[0] <= 1
        ), f"Found multiple hints for the return type: {arg_hint}"

        # no type hint, skip
        if rettypes.shape[0] == 0:
            logger.debug(f"No hint found for return for '{fdef.name}'")

        if rettypes.shape[0] == 1:
            ret_hint = rettypes[TraceData.VARTYPE].values[0]
            logger.debug(f"Applying return type hint '{ret_hint}' to '{fdef.name}'")
            fdef.returns = ast.Name(ret_hint)

        self.generic_visit(fdef)
        return fdef

    def visit_Assign(self, node: ast.Assign) -> ast.Assign | ast.AnnAssign | list[ast.AST]:
        if not node.value:
            return node

        target_names_with_nodes = list()
        for target in node.targets:
            target_names_with_nodes += self._extract_target_names_with_nodes(target)
        if len(target_names_with_nodes) == 0:
            return node

        target_names = [target_name_with_node[0] for target_name_with_node in target_names_with_nodes]

        logger.debug(f"Applying hints to '{target_names}'")

        class_name = None
        node_to_check = node
        while hasattr(node_to_check, "parent"):
            node_to_check = node_to_check.parent  # type: ignore
            if isinstance(node_to_check, ast.ClassDef):
                class_name = node_to_check.name
                break

        var_mask_local_variables = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[TraceData.VARNAME].isin(target_names),
            self.df[TraceData.LINENO] == node.lineno,
            self.df[TraceData.CLASS] == class_name,
        ]

        var_mask_class_members = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[TraceData.VARNAME].isin(target_names),
            self.df[TraceData.CLASS] == class_name,
        ]

        relevant_trace_data_local_variables = self.df[functools.reduce(operator.and_, var_mask_local_variables)]
        relevant_trace_data_class_member = self.df[functools.reduce(operator.and_, var_mask_class_members)]

        # Attach hint directly to assignment and promote to AnnAssign
        new_nodes: list[ast.AST] = []
        contains_one_target = len(target_names_with_nodes) == 1
        for target_name_with_node in target_names_with_nodes:
            target_name = target_name_with_node[0]
            target_node = target_name_with_node[1]
            target_trace_data = None
            if isinstance(target_node, ast.Attribute):
                # Finds the class member type hint.
                target_trace_data = relevant_trace_data_class_member[
                    relevant_trace_data_class_member[TraceData.VARNAME] == target_name]
            elif isinstance(target_node, ast.Name):
                # Finds the local variable type hint.
                target_trace_data = relevant_trace_data_local_variables[
                    relevant_trace_data_local_variables[TraceData.VARNAME] == target_name]
            if target_trace_data is None or len(target_trace_data) == 0:
                logger.debug(
                    f"No hint found for assign for '{target_name}'"
                )
                continue

            logger.debug(
                f"Applying type hints for simple assignment '{target_name}'"
            )
            if contains_one_target:
                new_node = ast.AnnAssign(
                    target_node,
                    value=node.value,
                    annotation=ast.Name(target_trace_data[TraceData.VARTYPE].values[0]),
                    simple=True,
                )
                return new_node
            else:
                new_node = ast.AnnAssign(
                    target_node,
                    annotation=ast.Name(target_trace_data[TraceData.VARTYPE].values[0]),
                    simple=True
                )

            new_nodes.append(new_node)

        new_nodes.append(node)
        return new_nodes

    def _extract_target_names_with_nodes(self, node: ast.AST) -> list[tuple[str, ast.Name | ast.Attribute]]:
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
                target_names_with_nodes_in_child_node = self._extract_target_names_with_nodes(child_node)
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
