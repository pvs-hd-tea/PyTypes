from dataclasses import dataclass
import functools
import itertools
import logging
import operator
import os
import pathlib
from typing import NoReturn
import typing

import pandas as pd
import libcst as cst
from libcst.metadata import PositionProvider

from constants import Column
from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator

logger = logging.getLogger(__name__)


@dataclass
class Targets:
    names: list[tuple[str, cst.Name]]
    attrs: list[tuple[str, cst.Attribute]]


class TargetExtractor(cst.CSTVisitor):
    targets: Targets

    def __init__(self):
        self.targets = Targets(list(), list())

    def visit_Attribute(self, node: cst.Attribute) -> bool | None:
        self.targets.attrs.append((node.attr.value, node))
        return False

    def visit_Name(self, node: cst.Name) -> bool | None:
        self.targets.names.append((node.value, node))
        return False


def _find_targets(
    node: cst.Assign | cst.AnnAssign | cst.AugAssign,
) -> Targets:
    extractor = TargetExtractor()
    if isinstance(node, cst.AnnAssign | cst.AugAssign):
        node.target.visit(extractor)
    else:
        for target in node.targets:
            target.visit(extractor)
    return extractor.targets


def _create_annotation_from_vartype(vartype: str) -> cst.Annotation:
    return cst.Annotation(annotation=cst.parse_expression(vartype))


class TypeHintTransformer(cst.CSTTransformer):
    """Transforms the CST by adding the traced type hints without modifying the original type hints."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, module: str, relevant: pd.DataFrame) -> None:
        super().__init__()

        # corner case: NoneType can be hinted with None to avoid needing an import
        self.df = relevant.copy()

        builtin_mask = self.df[Column.VARTYPE_MODULE].isnull()
        nonetype_mask = self.df[Column.VARTYPE] == "NoneType"

        mask = functools.reduce(operator.and_, [builtin_mask, nonetype_mask])
        self.df.loc[mask, Column.VARTYPE] = "None"

        self._module = module
        self._scope_stack: list[cst.FunctionDef | cst.ClassDef] = []

        self._globals_by_scope: dict[cst.FunctionDef, set[str]] = {}

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

    def _find_visible_globals(
        self, node: cst.Assign | cst.AnnAssign | cst.AugAssign
    ) -> typing.Iterator[str]:
        fromtop = reversed(self._scope_stack)

        # tee copies the iterator, avoid death by mutable reference
        # there is no rewinding of iterators sadly
        fdefs, tester = itertools.tee(
            filter(lambda p: isinstance(p, cst.FunctionDef), fromtop)
        )

        # Check if this IS global scope
        if next(tester, None) is None:
            # We are in the global scope -> any variable written on this line must be a global!
            # Only consider names, as we are outside of class scope, and we shall not annotate
            # class attributes outside of said class
            logger.debug(
                "This is global scope; Using the variables on the given line as globals!"
            )
            yield from map(operator.itemgetter(0), _find_targets(node).names)

        # Advance iterator and collect globals
        # mypy fails to narrow the fdef type here
        SENTINEL: set[str] = set()
        yield from (
            glbl
            for fdef in fdefs
            for glbl in self._globals_by_scope.get(fdef, SENTINEL)  # type: ignore
        )

    def _get_trace_for_targets(
        self, node: cst.Assign | cst.AnnAssign | cst.AugAssign
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Targets]:
        """
        Fetches trace data for the targets from the given assignment statement.
        Return order is (global variables, local variables, class attributes, targets)
        """
        targets = _find_targets(node)

        # Skip the globals
        glbls = set(self._find_visible_globals(node))
        local_var_idents = list()
        global_var_idents = list()

        for ident, _ in targets.names:
            if ident not in glbls:
                logger.debug(f"Interpreted {ident} as a local variable")
                local_var_idents.append(ident)
            else:
                logger.debug(f"Interpreted {ident} as a global variable")
                global_var_idents.append(ident)

        attr_idents = list(map(operator.itemgetter(0), targets.attrs))

        containing_classes: list[cst.ClassDef] = []

        # Crawl over class stack and analyse available attributes
        # Iterate in reverse to match scope resolution order
        for scope in reversed(self._scope_stack):
            if isinstance(scope, cst.ClassDef):
                containing_classes.append(scope)

        if not len(containing_classes):
            class_mask = self.df[Column.CLASS].isnull()
            class_module_mask = self.df[Column.CLASS_MODULE].isnull()
        else:
            class_names = list(map(lambda c: c.name.value, containing_classes))
            class_mask = self.df[Column.CLASS].isin(class_names)

            # This column can only ever contain project files, as we never
            # trace the internals of files outside of the given project
            # (i.e. no stdlib, no venv etc.), so this check is safe
            class_module_mask = self.df[Column.CLASS_MODULE] == self._module

        pos = self.get_metadata(PositionProvider, node).start

        local_var_mask = [
            class_module_mask,
            class_mask,
            self.df[Column.LINENO] == pos.line,
            self.df[Column.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[Column.VARNAME].isin(local_var_idents),
        ]
        attr_mask = [
            class_module_mask,
            class_mask,
            self.df[Column.LINENO] == 0,
            self.df[Column.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[Column.VARNAME].isin(attr_idents),
        ]

        global_var_mask = [
            self.df[Column.CLASS_MODULE].isnull(),
            self.df[Column.CLASS].isnull(),
            self.df[Column.LINENO] == 0,
            self.df[Column.CATEGORY] == TraceDataCategory.GLOBAL_VARIABLE,
            self.df[Column.VARNAME].isin(global_var_idents),
        ]

        local_vars = self.df[functools.reduce(operator.and_, local_var_mask)]
        attrs = self.df[functools.reduce(operator.and_, attr_mask)]
        global_vars = self.df[functools.reduce(operator.and_, global_var_mask)]

        return global_vars, local_vars, attrs, targets

    def _get_trace_for_param(self, node: cst.Param) -> pd.DataFrame:
        # Retrieve outermost function from parent stack
        fdef = self._innermost_function()
        assert (
            fdef is not None
        ), f"param {node.name.value} has not been associated with a function"

        pos = self.get_metadata(PositionProvider, node).start
        param_name = node.name.value

        param_masks = [
            self.df[Column.CATEGORY] == TraceDataCategory.FUNCTION_PARAMETER,
            self.df[Column.FUNCNAME] == fdef.name.value,
            self.df[Column.LINENO] == pos.line,
            self.df[Column.VARNAME] == param_name,
        ]
        params = self.df[functools.reduce(operator.and_, param_masks)]
        return params

    def _get_trace_for_rettype(self, node: cst.FunctionDef) -> pd.DataFrame:
        # Retrieve outermost class from parent stack
        # to disambig. methods and functions
        cdef = self._innermost_class()
        if cdef is not None:
            clazz_mask = self.df[Column.CLASS] == cdef.name.value
            class_module_mask = self.df[Column.CLASS_MODULE] == self._module
        else:
            clazz_mask = self.df[Column.CLASS].isnull()
            class_module_mask = self.df[Column.CLASS_MODULE].isnull()

        rettype_masks = [
            class_module_mask,
            clazz_mask,
            self.df[Column.LINENO] == 0,  # return type, always stored at line 0
            self.df[Column.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
            self.df[Column.VARNAME] == node.name.value,
        ]
        rettypes = self.df[functools.reduce(operator.and_, rettype_masks)]
        return rettypes

    def visit_ClassDef(self, cdef: cst.ClassDef) -> bool | None:
        logger.debug(f"Entering class '{cdef.name.value}'")

        # Track ClassDefs to disambiguate functions from methods
        self._scope_stack.append(cdef)
        return True

    def leave_ClassDef(self, _: cst.ClassDef, updated: cst.ClassDef) -> cst.ClassDef:
        logger.debug(f"Leaving class '{updated.name.value}'")

        self._scope_stack.pop()
        return updated

    def visit_FunctionDef(self, fdef: cst.FunctionDef) -> bool | None:
        logger.debug(f"Entering function '{fdef.name.value}'")
        self._scope_stack.append(fdef)
        return True

    def visit_Global(self, node: cst.Global) -> bool | None:
        names = set(map(lambda n: n.name.value, node.names))
        logger.debug(f"Found globals: '{names}'")

        fdef = self._innermost_function()
        assert fdef is not None

        # globals are global for the scope they are currently part of
        self._globals_by_scope[fdef] = names
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        logger.debug(f"Leaving FunctionDef '{original_node.name.value}'")
        self._scope_stack.pop()

        if original_node in self._globals_by_scope:
            del self._globals_by_scope[original_node]

        rettypes = self._get_trace_for_rettype(original_node)

        if rettypes.shape[0] > 1:
            self._on_multiple_hints_found(
                original_node.name.value, rettypes, original_node
            )

        returns: cst.Annotation | None

        # no type hint, skip
        if rettypes.empty:
            logger.debug(f"No return type hint found for {original_node.name.value}")
            return updated_node
        else:
            rettype = rettypes[Column.VARTYPE].values[0]
            assert rettype is not None

            logger.debug(
                f"Applying return type hint '{rettype}' to '{original_node.name.value}'"
            )
            returns = cst.Annotation(cst.Name(rettype))

        return updated_node.with_changes(returns=returns)

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        params = self._get_trace_for_param(original_node)
        if params.shape[0] > 1:
            self._on_multiple_hints_found(
                updated_node.name.value,
                params,
                original_node,
            )

        if updated_node.annotation is not None:
            logger.debug(
                f"'{original_node.name.value}' already has an annotation, returning."
            )
            return updated_node

        # no type hint, skip
        if params.empty:
            logger.debug(f"No hint found for parameter '{original_node.name.value}'")
            return updated_node

        argtype = params[Column.VARTYPE].values[0]
        assert argtype is not None

        logger.debug(
            f"Applying hint '{argtype}' to parameter '{original_node.name.value}'"
        )
        return updated_node.with_changes(
            annotation=_create_annotation_from_vartype(argtype)
        )

    def leave_AugAssign(
        self, original_node: cst.AugAssign, _: cst.AugAssign
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        global_vars, local_vars, class_members, targets = self._get_trace_for_targets(
            original_node
        )
        hinted_targets: list[cst.BaseSmallStatement] = []

        all_globals_in_scope = set(self._find_visible_globals(original_node))

        for ident, var in itertools.chain(targets.attrs, targets.names):
            if isinstance(var, cst.Name) and ident in all_globals_in_scope:
                logger.debug(f"Searching for '{ident}' in global variables")
                hinted = global_vars[global_vars[Column.VARNAME] == ident]
            elif isinstance(var, cst.Name):
                logger.debug(f"Searching for '{ident}' in local variables")
                hinted = local_vars[local_vars[Column.VARNAME] == ident]
            else:
                logger.debug(f"Searching for '{ident}' in class attributes")
                hinted = class_members[class_members[Column.VARNAME] == ident]

            if hinted.shape[0] > 1:
                self._on_multiple_hints_found(ident, hinted, original_node)

            if hinted.empty:
                logger.debug(f"No type hint stored for {ident} in AugAssign")
                logger.debug("Not adding AnnAssign for AugAssign")
                continue

            hint = hinted[Column.VARTYPE].values[0]
            assert hint is not None

            hinted_targets.append(
                cst.AnnAssign(
                    target=original_node.target,
                    annotation=cst.Annotation(cst.Name(value=hint)),
                    value=None,
                )
            )

        hinted_targets.append(original_node)
        return cst.FlattenSentinel(hinted_targets)

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign | cst.AnnAssign | cst.FlattenSentinel[cst.BaseSmallStatement]:
        global_vars, local_vars, class_members, targets = self._get_trace_for_targets(
            original_node
        )
        all_globals_in_scope = set(self._find_visible_globals(original_node))

        logger.debug(f"Set: {all_globals_in_scope}")
        logger.debug(f"DataFrame:\n{global_vars}")

        if len(targets.names) + len(targets.attrs) > 1:
            hinted_targets: list[cst.BaseSmallStatement] = []
            for ident, var in itertools.chain(targets.attrs, targets.names):
                if isinstance(var, cst.Name) and ident in all_globals_in_scope:
                    logger.debug(f"Searching for '{ident}' in global variables")
                    hinted = global_vars[global_vars[Column.VARNAME] == ident]
                elif isinstance(var, cst.Name):
                    logger.debug(f"Searching for '{ident}' in local variables")
                    hinted = local_vars[local_vars[Column.VARNAME] == ident]
                else:
                    logger.debug(f"Searching for '{ident}' in class attributes")
                    hinted = class_members[class_members[Column.VARNAME] == ident]

                if hinted.shape[0] > 1:
                    self._on_multiple_hints_found(ident, hinted, original_node)

                if hinted.empty:
                    if isinstance(var, cst.Attribute):
                        logger.debug(
                            f"Skipping hint for {ident}, as annotating \
                            class members externally is forbidden"
                        )
                    else:
                        logger.debug(f"Hint for {ident} could not be found")

                    logger.debug("Not adding AnnAssign for Assign")
                    continue

                else:
                    hint_ty = hinted[Column.VARTYPE].values[0]
                    assert hint_ty is not None

                    logger.debug(f"Found '{hint_ty}' for '{ident}'")
                    hinted_targets.append(
                        cst.AnnAssign(
                            target=var,
                            annotation=_create_annotation_from_vartype(hint_ty),
                            value=None,
                        )
                    )

            hinted_targets.append(original_node)
            return cst.FlattenSentinel(hinted_targets)

        ident, var = next(itertools.chain(targets.attrs, targets.names))
        if isinstance(var, cst.Name) and ident in all_globals_in_scope:
            logger.debug(f"Searching for '{ident}' in global variables")
            hinted = global_vars[global_vars[Column.VARNAME] == ident]
        elif isinstance(var, cst.Name):
            logger.debug(f"Searching for '{ident}' in local variables")
            hinted = local_vars[local_vars[Column.VARNAME] == ident]
        else:
            logger.debug(f"Searching for '{ident}' in class attributes")
            hinted = class_members[class_members[Column.VARNAME] == ident]

        if hinted.shape[0] > 1:
            self._on_multiple_hints_found(ident, hinted, original_node)

        if hinted.empty:
            logger.debug(f"No hints found for '{ident}'")
            logger.debug("Not adding type hint annotation for Assign")
            return updated_node

        hint_ty = hinted[Column.VARTYPE].values[0]
        assert hint_ty is not None

        logger.debug(
            f"Replacing Assign for '{ident}' with AnnAssign with hint '{hint_ty}'"
        )

        # Replace simple assignment with annotated assignment
        return cst.AnnAssign(
            target=original_node.targets[0].target,
            annotation=_create_annotation_from_vartype(hint_ty),
            value=original_node.value,
        )

    def leave_AnnAssign(
        self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
    ) -> cst.Assign | cst.AnnAssign | cst.RemovalSentinel:
        global_var, local_var, class_member, targets = self._get_trace_for_targets(
            original_node
        )

        # only one target is possible
        tgt_cnt = len(targets.attrs) + len(targets.names)
        assert tgt_cnt == 1, f"Only exactly one target is possible, found {tgt_cnt}"

        ident, ident_node = next(itertools.chain(targets.attrs, targets.names))
        logger.debug(f"Searching for hints to '{ident}' for an AnnAssign")

        if isinstance(ident_node, cst.Name):
            hinted = local_var if not local_var.empty else global_var
        else:
            hinted = class_member

        if hinted.shape[0] > 1:
            self._on_multiple_hints_found(ident, hinted, original_node)

        if hinted.empty and original_node.value is None:
            logger.debug(
                "Removing AnnAssign without value because no type hint can be provided"
            )
            return cst.RemoveFromParent()

        elif hinted.empty and original_node.value is not None:
            logger.debug(
                "Replacing AnnAssign with value by Assign without type hint because no type hint can be provided"
            )
            return cst.Assign(
                targets=[cst.AssignTarget(original_node.target)],
                value=original_node.value,
            )

        else:
            hint_ty = hinted[Column.VARTYPE].values[0]
            assert hint_ty is not None

            logger.debug(f"Using '{hint_ty}' for the AnnAssign with '{ident}'")

            # Replace simple assignment with annotated assignment
            return updated_node.with_changes(
                target=original_node.target,
                annotation=cst.Annotation(cst.Name(value=hint_ty)),
                value=original_node.value,
            )

    def _on_multiple_hints_found(
        self, ident: str, hints_found: pd.DataFrame, node: cst.CSTNode
    ) -> NoReturn:
        try:
            stringified = cst.Module([]).code_for_node(node)
        except AttributeError:
            stringified = node.__class__.__name__
        file = self.df[Column.FILENAME].values[0]
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            raise ValueError(
                f"In {file}: found more than one type hint for {ident}\nNode: {stringified}\n{hints_found}"
            )


class InlineGenerator(TypeHintGenerator):
    ident = "inline"

    def _transformers(self, module_path: str, applicable: pd.DataFrame) -> list[cst.CSTTransformer]:
        return [
            TypeHintTransformer(module_path, applicable)
        ]

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Inline means overwriting the original
        contents = hinting.code
        with source_file.open("w") as f:
            f.write(contents)

