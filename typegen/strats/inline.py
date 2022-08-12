from dataclasses import dataclass
import functools
import itertools
import logging
import operator
import os
import pathlib

import pandas as pd
import libcst as cst
from libcst.metadata import PositionProvider

from constants import TraceData
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


class TypeHintTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, module: str, relevant: pd.DataFrame) -> None:
        super().__init__()
        self.df = relevant
        self._module = module
        self._scope_stack: list[cst.FunctionDef | cst.ClassDef] = []

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

    def _get_trace_for_targets(
        self, node: cst.Assign | cst.AnnAssign | cst.AugAssign
    ) -> tuple[pd.DataFrame, pd.DataFrame, Targets]:
        """
        Fetches trace data for the targets from the given assignment statement.
        If the statement references members of classes, but is NOT within a
        method of a class with these members, then we do not NOT return their data.

        Return order is (variables, class attributes, targets)
        """
        targets = _find_targets(node)
        name_idents = list(map(operator.itemgetter(0), targets.names))
        attr_idents = list(map(operator.itemgetter(0), targets.attrs))

        containing_classes: list[cst.ClassDef] = []

        # Crawl over class stack and analyse available attributes
        # Iterate in reverse to match scope resolution order
        for scope in reversed(self._scope_stack):
            if isinstance(scope, cst.ClassDef):
                containing_classes.append(scope)

        if not len(containing_classes):
            class_mask = self.df[TraceData.CLASS].isnull()
            class_module_mask = self.df[TraceData.CLASS_MODULE].isnull()
        else:
            class_names = list(map(lambda c: c.name.value, containing_classes))
            class_mask = self.df[TraceData.CLASS].isin(class_names)

            # This column can only ever contain project files, as we never
            # trace the internals of files outside of the given project
            # (i.e. no stdlib, no venv etc.), so this check is safe
            class_module_mask = self.df[TraceData.CLASS_MODULE] == self._module

        pos = self.get_metadata(PositionProvider, node).start
        name_mask = [
            class_module_mask,
            class_mask,
            self.df[TraceData.LINENO] == pos.line,
            self.df[TraceData.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[TraceData.VARNAME].isin(name_idents),
        ]
        attr_mask = [
            class_module_mask,
            class_mask,
            self.df[TraceData.LINENO] == 0,
            self.df[TraceData.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[TraceData.VARNAME].isin(attr_idents),
        ]

        names = self.df[functools.reduce(operator.and_, name_mask)]
        attrs = self.df[functools.reduce(operator.and_, attr_mask)]

        return names, attrs, targets

    def _get_trace_for_param(self, node: cst.Param) -> pd.DataFrame:
        # Retrieve outermost function from parent stack
        fdef = self._innermost_function()
        assert (
            fdef is not None
        ), f"param {node.name.value} has not been associated with a function"

        pos = self.get_metadata(PositionProvider, node).start
        param_name = node.name.value

        param_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_PARAMETER,
            self.df[TraceData.FUNCNAME] == fdef.name.value,
            self.df[TraceData.LINENO] == pos.line,
            self.df[TraceData.VARNAME] == param_name,
        ]
        params = self.df[functools.reduce(operator.and_, param_masks)]
        return params

    def _get_trace_for_rettype(self, node: cst.FunctionDef) -> pd.DataFrame:
        # Retrieve outermost class from parent stack
        # to disambig. methods and functions
        cdef = self._innermost_class()
        if cdef is not None:
            clazz_mask = self.df[TraceData.CLASS] == cdef.name.value
            class_module_mask = self.df[TraceData.CLASS_MODULE] == self._module
        else:
            clazz_mask = self.df[TraceData.CLASS].isnull()
            class_module_mask = self.df[TraceData.CLASS_MODULE].isnull()

        rettype_masks = [
            class_module_mask,
            clazz_mask,
            self.df[TraceData.LINENO] == 0,  # return type, always stored at line 0
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
            self.df[TraceData.VARNAME] == node.name.value,
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

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        rettypes = self._get_trace_for_rettype(original_node)

        assert (
            rettypes.shape[0] <= 1
        ), f"Found multiple hints for the return type:\n{rettypes[TraceData.VARTYPE].values}"

        returns: cst.Annotation | None

        # no type hint, skip
        if rettypes.empty:
            logger.debug(f"No return type hint found for {original_node.name.value}")
            logger.debug(
                f"Removing any previous return type annotation on FunctionDef '{original_node.name.value}'"
            )
            returns = None

        else:
            rettype = rettypes[TraceData.VARTYPE].values[0]
            assert rettype is not None

            logger.debug(
                f"Applying return type hint '{rettype}' to '{original_node.name.value}'"
            )
            logger.debug(f"Leaving FunctionDef '{original_node.name.value}'")
            returns = cst.Annotation(cst.Name(rettype))

        self._scope_stack.pop()
        return updated_node.with_changes(returns=returns)

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        params = self._get_trace_for_param(original_node)
        arg_hints = params[TraceData.VARNAME]
        assert (
            arg_hints.shape[0] <= 1
        ), f"Found multiple hints for the parameter type: {arg_hints}"

        # no type hint, skip
        if arg_hints.empty:
            logger.debug(f"No hint found for parameter '{original_node.name.value}'")
            logger.debug("Removing any previous return type annotation on parameter")
            return updated_node.with_changes(annotation=None)

        argtype = params[TraceData.VARTYPE].values[0]
        assert argtype is not None

        logger.debug(
            f"Applying hint '{argtype}' to parameter '{original_node.name.value}'"
        )
        return updated_node.with_changes(annotation=cst.Annotation(cst.Name(argtype)))

    def leave_AugAssign(
        self, original_node: cst.AugAssign, _: cst.AugAssign
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        local_vars, class_members, targets = self._get_trace_for_targets(original_node)
        hinted_targets: list[cst.BaseSmallStatement] = []

        for ident, var in itertools.chain(targets.attrs, targets.names):
            if isinstance(var, cst.Name):
                hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
            else:
                hinted = class_members[class_members[TraceData.VARNAME] == ident]

            assert (
                hinted.shape[0] <= 1
            ), f"Found more than one type hint for {ident}: \n{hinted}"

            if hinted.empty:
                logger.debug(f"No type hint stored for {ident} in AugAssign")
                logger.debug("Not adding AnnAssign for AugAssign")
                continue

            hint = hinted[TraceData.VARTYPE].values[0]
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
        local_vars, class_members, targets = self._get_trace_for_targets(original_node)

        if len(targets.names) + len(targets.attrs) > 1:
            hinted_targets: list[cst.BaseSmallStatement] = []
            for ident, var in itertools.chain(targets.attrs, targets.names):
                if isinstance(var, cst.Name):
                    logger.debug(f"Searching for '{ident}' in local variables")
                    hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
                else:
                    logger.debug(f"Searching for '{ident}' in class attributes")
                    hinted = class_members[class_members[TraceData.VARNAME] == ident]

                assert (
                    hinted.shape[0] <= 1
                ), f"Found more than one type hint for {ident}"

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
                    hint_ty = hinted[TraceData.VARTYPE].values[0]
                    assert hint_ty is not None

                    logger.debug(f"Found '{hint_ty}' for '{ident}'")
                    hinted_targets.append(
                        cst.AnnAssign(
                            target=var,
                            annotation=cst.Annotation(cst.Name(value=hint_ty)),
                            value=None,
                        )
                    )

            hinted_targets.append(original_node)
            return cst.FlattenSentinel(hinted_targets)

        ident, var = next(itertools.chain(targets.attrs, targets.names))
        if isinstance(var, cst.Name):
            hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
        else:
            hinted = class_members[class_members[TraceData.VARNAME] == ident]

        assert hinted.shape[0] <= 1, f"Found more than one type hint for '{ident}'"

        if hinted.empty:
            logger.debug(f"No hints found for '{ident}'")
            logger.debug("Not adding type hint annotation for Assign")
            return updated_node

        hint_ty = hinted[TraceData.VARTYPE].values[0]
        assert hint_ty is not None

        logger.debug(
            f"Replacing Assign for '{ident}' with AnnAssign with hint '{hint_ty}'"
        )

        # Replace simple assignment with annotated assignment
        return cst.AnnAssign(
            target=original_node.targets[0].target,
            annotation=cst.Annotation(cst.Name(value=hint_ty)),
            value=original_node.value,
        )

    def leave_AnnAssign(
        self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
    ) -> cst.Assign | cst.AnnAssign | cst.RemovalSentinel:
        local_var, class_member, targets = self._get_trace_for_targets(original_node)

        # only one target is possible
        tgt_cnt = len(targets.attrs) + len(targets.names)
        assert tgt_cnt == 1, f"Only exactly one target is possible, found {tgt_cnt}"

        ident, ident_node = next(itertools.chain(targets.attrs, targets.names))
        logger.debug(f"Searching for hints to '{ident}' for an Assign")

        hinted = local_var if isinstance(ident_node, cst.Name) else class_member
        assert hinted.shape[0] <= 1, f"Found more than one type hint for '{ident}'"

        if hinted.empty and original_node.value is None:
            logger.debug(
                "Removing AnnAssign without value \
                    because no type hint can be provided"
            )
            return cst.RemoveFromParent()

        elif hinted.empty and original_node.value is not None:
            logger.debug(
                "Replacing AnnAssign with value by Assign without type hint \
                    because no type hint can be provided"
            )
            return cst.Assign(
                targets=[cst.AssignTarget(original_node.target)],
                value=original_node.value,
            )

        else:
            hint_ty = hinted[TraceData.VARTYPE].values[0]
            assert hint_ty is not None

            logger.debug(f"Using '{hint_ty}' for the AnnAssign with '{ident}'")

            # Replace simple assignment with annotated assignment
            return updated_node.with_changes(
                target=original_node.target,
                annotation=cst.Annotation(cst.Name(value=hint_ty)),
                value=original_node.value,
            )


class InlineGenerator(TypeHintGenerator):
    ident = "inline"

    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, hintless_ast: cst.MetadataWrapper
    ) -> cst.Module:
        # Access is safe, as check in base class guarantees at least one element
        filename = applicable[TraceData.FILENAME].values[0]
        assert filename is not None

        path = os.path.splitext(filename)[0]
        as_module = path.replace(os.path.sep, ".")

        visitor = TypeHintTransformer(as_module, applicable)
        hinted = hintless_ast.visit(visitor)

        return hinted

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Inline means overwriting the original
        contents = hinting.code
        with source_file.open("w") as f:
            f.write(contents)
