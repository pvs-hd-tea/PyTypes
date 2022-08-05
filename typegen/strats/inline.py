import functools
import logging
import operator
import pathlib

import pandas as pd

import libcst as cst

from libcst.metadata import PositionProvider

from constants import TraceData
from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator

logger = logging.getLogger(__name__)


class TargetExtractor(cst.CSTVisitor):
    targets: list[tuple[str, cst.Name | cst.Attribute]]

    def __init__(self):
        self.targets = list()

    def visit_Attribute(self, node: cst.Attribute) -> bool | None:
        self.targets.append((node.attr.value, node))
        return False

    def visit_Name(self, node: cst.Name) -> bool | None:
        self.targets.append((node.value, node))
        return False


class TypeHintTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, relevant: pd.DataFrame) -> None:
        super().__init__()
        self.df = relevant
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

    def _find_targets(
        self, node: cst.Assign | cst.AnnAssign | cst.AugAssign
    ) -> list[tuple[str, cst.Name | cst.Attribute]]:
        extractor = TargetExtractor()
        if isinstance(node, cst.AnnAssign | cst.AugAssign):
            node.target.visit(extractor)
        else:
            for target in node.targets:
                target.visit(extractor)
        return extractor.targets

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
        # Track assignments from Functions
        # NOTE: this handles nested functions too, because the parent reference gets overwritten
        # NOTE: before we start generating hints for its children
        """for direct in cst.iter_child_nodes(fdef):
        for child in cst.walk(direct):  # type: ignore
            child.parent = node  # type: ignore"""
        logger.debug(f"Entering function '{fdef.name.value}'")
        self._scope_stack.append(fdef)
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        # Retrieve outermost class from parent stack
        # to disambig. methods and functions

        cdef = self._innermost_class()
        if cdef is not None:
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            clazz_mask = names == cdef.name.value
        else:
            clazz_mask = self.df[TraceData.CLASS].isnull()

        rettype_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_RETURN,
            clazz_mask,
            self.df[TraceData.VARNAME] == original_node.name.value,
            self.df[TraceData.LINENO] == 0,  # return type, always stored at line 0
        ]
        rettypes = self.df[functools.reduce(operator.and_, rettype_masks)]

        assert (
            rettypes.shape[0] <= 1
        ), f"Found multiple hints for the return type:\n{rettypes[TraceData.VARTYPE].values}"

        # no type hint, skip
        if rettypes.empty:
            logger.debug(f"No return type hint found for {original_node.name.value}")
            logger.debug(f"Leaving FunctionDef '{original_node.name.value}'")
            return updated_node

        else:
            rettype = rettypes[TraceData.VARTYPE].values[0]
            assert rettype is not None

            ret_hint = rettype.__name__
            logger.debug(
                f"Applying return type hint '{ret_hint}' to '{original_node.name.value}'"
            )
            logger.debug(f"Leaving FunctionDef '{original_node.name.value}'")
            return updated_node.with_changes(returns=cst.Annotation(cst.Name(ret_hint)))

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        # Retrieve outermost function from parent stack
        fdef = self._innermost_function()
        assert (
            fdef is not None
        ), f"param {original_node.name.value} has not been associated with a function"

        pos = self.get_metadata(PositionProvider, original_node).start
        param_name = original_node.name.value

        param_masks = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.FUNCTION_PARAMETER,
            self.df[TraceData.FUNCNAME] == fdef.name.value,
            self.df[TraceData.LINENO] == pos.line,
            self.df[TraceData.VARNAME] == param_name,
        ]
        params = self.df[functools.reduce(operator.and_, param_masks)]

        arg_hints = params[TraceData.VARNAME]
        assert (
            arg_hints.shape[0] <= 1
        ), f"Found multiple hints for the parameter type: {arg_hints}"

        # no type hint, skip
        if arg_hints.empty:
            logger.debug(f"No hint found for parameter '{original_node.name.value}'")
            return updated_node

        argtype = params[TraceData.VARTYPE].values[0]
        assert argtype is not None

        arg_hint = argtype.__name__
        logger.debug(
            f"Applying hint '{arg_hint}' to parameter '{original_node.name.value}'"
        )
        return updated_node.with_changes(annotation=cst.Annotation(cst.Name(arg_hint)))

    def leave_AugAssign(
        self, original_node: cst.AugAssign, _: cst.AugAssign
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        targets = self._find_targets(original_node)
        target_idents = list(map(operator.itemgetter(0), targets))

        logger.debug(f"Applying hints to '{', '.join(target_idents)}' for an AugAssign")

        cdef = self._innermost_class()
        if cdef is not None:
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            class_check = names == cdef.name.value
        else:
            class_check = self.df[TraceData.CLASS].isnull()

        pos = self.get_metadata(PositionProvider, original_node).start
        var_mask_local_variables = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[TraceData.VARNAME].isin(target_idents),
            self.df[TraceData.LINENO] == pos.line,
            class_check,
        ]

        var_mask_class_members = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[TraceData.VARNAME].isin(target_idents),
            self.df[TraceData.FUNCNAME] == "",
            self.df[TraceData.LINENO] == 0,
            class_check,
        ]

        local_vars = self.df[functools.reduce(operator.and_, var_mask_local_variables)]
        class_members = self.df[functools.reduce(operator.and_, var_mask_class_members)]

        hinted_targets: list[cst.BaseSmallStatement] = []

        for ident, var in targets:
            if isinstance(var, cst.Name):
                hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
            else:
                hinted = class_members[class_members[TraceData.VARNAME] == ident]

            assert (
                hinted.shape[0] <= 1
            ), f"Found more than one type hint for {ident}: \n{hinted}"

            if hinted.empty:
                logger.debug(f"No type hint stored for {ident} in AugAssign")
                continue

            hint_ty = hinted[TraceData.VARTYPE].values[0]
            assert hint_ty is not None
            hint = hint_ty.__name__

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
        targets = self._find_targets(original_node)
        target_idents = list(map(operator.itemgetter(0), targets))

        logger.debug(
            f"Searching for hints to '{', '.join(target_idents)}' for an Assign"
        )

        cdef = self._innermost_class()
        if cdef is not None:
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            class_check = names == cdef.name.value
        else:
            class_check = self.df[TraceData.CLASS].isnull()

        pos = self.get_metadata(PositionProvider, original_node).start
        local_vars_mask = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.LOCAL_VARIABLE,
            self.df[TraceData.VARNAME].isin(target_idents),
            self.df[TraceData.LINENO] == pos.line,
            class_check,
        ]

        class_member_mask = [
            self.df[TraceData.CATEGORY] == TraceDataCategory.CLASS_MEMBER,
            self.df[TraceData.VARNAME].isin(target_idents),
            self.df[TraceData.FUNCNAME] == "",
            self.df[TraceData.LINENO] == 0,
            class_check,
        ]

        local_vars = self.df[functools.reduce(operator.and_, local_vars_mask)]
        class_members = self.df[functools.reduce(operator.and_, class_member_mask)]

        if len(targets) > 1:
            hinted_targets: list[cst.BaseSmallStatement] = []
            for ident, var in targets:
                if isinstance(var, cst.Name):
                    logger.debug(f"Searching for {ident} in local variables")
                    hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
                else:
                    logger.debug(f"Searching for {ident} in class attributes")
                    hinted = class_members[class_members[TraceData.VARNAME] == ident]

                assert (
                    hinted.shape[0] <= 1
                ), f"Found more than one type hint for {ident}"

                if hinted.empty:
                    logger.debug(f"No hint found for {ident}")
                    continue

                else:
                    hint_ty = hinted[TraceData.VARTYPE].values[0]
                    assert hint_ty is not None
                    hint = hint_ty.__name__

                    logger.debug(f"Found {hint} for {ident}")
                    hinted_targets.append(
                        cst.AnnAssign(
                            target=var,
                            annotation=cst.Annotation(cst.Name(value=hint)),
                            value=None,
                        )
                    )

            hinted_targets.append(original_node)
            return cst.FlattenSentinel(hinted_targets)

        ident, var = targets[0]
        if isinstance(var, cst.Name):
            hinted = local_vars[local_vars[TraceData.VARNAME] == ident]
        else:
            hinted = class_members[class_members[TraceData.VARNAME] == ident]

        assert hinted.shape[0] <= 1, f"Found more than one type hint for '{ident}'"

        if hinted.empty:
            logger.debug(f"No hints found for '{ident}'")
            return updated_node

        hint_ty = hinted[TraceData.VARTYPE].values[0]
        assert hint_ty is not None
        hint = hint_ty.__name__

        logger.debug(
            f"Replacing Assign for '{ident}' with AnnAssign with hint '{hint}'"
        )

        # Replace simple assignment with annotated assignment
        return cst.AnnAssign(
            target=original_node.targets[0].target,
            annotation=cst.Annotation(cst.Name(value=hint)),
            value=original_node.value,
        )


class InlineGenerator(TypeHintGenerator):
    ident = "inline"

    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, wrapper: cst.MetadataWrapper
    ) -> cst.Module:
        visitor = TypeHintTransformer(applicable)
        hinted = wrapper.visit(visitor)

        return hinted

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Inline means overwriting the original
        contents = hinting.code
        with source_file.open("w") as f:
            f.write(contents)
