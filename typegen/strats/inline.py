import functools
import logging
import libcst as cst
from libcst.metadata.position_provider import PositionProvider
import operator
import pathlib

from constants import TraceData
from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator

import pandas as pd

logger = logging.getLogger(__name__)


class TargetExtractor(cst.CSTVisitor):
    targets: list[tuple[str, cst.Name | cst.Attribute]]

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
        self._parent_stack: list[cst.FunctionDef | cst.ClassDef] = []

    def _outermost_class(self) -> cst.ClassDef | None:
        fromtop = reversed(self._parent_stack)
        classes = filter(lambda p: isinstance(p, cst.ClassDef), fromtop)

        first: cst.ClassDef | None = next(classes, None)  # type: ignore
        return first

    def _outermost_function(self) -> cst.FunctionDef | None:
        fromtop = reversed(self._parent_stack)
        fdefs = filter(lambda p: isinstance(p, cst.FunctionDef), fromtop)

        first: cst.FunctionDef | None = next(fdefs, None)  # type: ignore
        return first

    def visit_ClassDef(self, cdef: cst.ClassDef) -> bool | None:
        # Track ClassDefs methods to disambiguate functions from methods
        self._parent_stack.append(cdef)
        return True

    def leave_ClassDef(self, _: cst.ClassDef, updated: cst.ClassDef) -> cst.ClassDef:
        self._parent_stack.pop()
        return updated

    def visit_FunctionDef(self, fdef: cst.FunctionDef) -> bool | None:
        # Track assignments from Functions
        # NOTE: this handles nested functions too, because the parent reference gets overwritten
        # NOTE: before we start generating hints for its children
        """for direct in cst.iter_child_nodes(fdef):
        for child in cst.walk(direct):  # type: ignore
            child.parent = node  # type: ignore"""
        logger.debug(f"Applying hints to '{fdef.name.value}'")
        self._parent_stack.append(fdef)
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        # Retrieve outermost class from parent stack
        # to disambig. methods and functions
        peeking = reversed(self._parent_stack)
        cdef = next(
            filter(lambda p: isinstance(p, cst.ClassDef), peeking),
            None,
        )
        if cdef is not None:
            clazz_name = cdef.name.value
            names = self.df[TraceData.CLASS].map(lambda t: t.__name__ if t else None)
            clazz_mask = names == clazz_name
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
        if rettypes.shape[0] == 0:
            logger.debug(f"No return type hint found for {original_node.name.value}")
            return original_node

        else:
            rettype = rettypes[TraceData.VARTYPE].values[0]
            assert rettype is not None

            ret_hint = rettype.__name__
            logger.debug(
                f"Applying return type hint '{ret_hint}' to '{original_node.name.value}'"
            )

            return updated_node.with_changes(returns=cst.Annotation(cst.Name(ret_hint)))

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        # Retrieve outermost function from parent stack
        fdef = self._outermost_function()
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
        if arg_hints.shape[0] == 0:
            logger.debug(f"No hint found for '{original_node.name.value}'")
            return original_node

        argtype = arg_hints[TraceData.VARTYPE].values[0]
        assert argtype is not None

        arg_hint = argtype.__name__
        logger.debug(f"Applying hint '{arg_hint}' to '{original_node.name.value}'")
        return updated_node.with_changes(annotation=cst.Annotation(cst.Name(arg_hint)))

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

    def leave_AugAssign(
        self, original_node: cst.AugAssign, _: cst.AugAssign
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        targets = self._find_targets(original_node)
        target_idents = list(map(operator.itemgetter(0), targets))

        logger.debug(f"Applying hints to '{target_idents} for an AugAssign'")

        cdef = self._outermost_class()
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
            self.df[TraceData.LINENO] == pos.line,
            class_check,
        ]

        local_vars = self.df[functools.reduce(operator.and_, var_mask_local_variables)]
        class_members = self.df[functools.reduce(operator.and_, var_mask_class_members)]

        hinted_targets: list[cst.BaseSmallStatement] = []

        for ident, var in targets:
            if isinstance(var, cst.Name):
                hinted = local_vars[TraceData.VARNAME] == ident
            else:
                hinted = class_members[TraceData.VARNAME] == ident

            assert hinted.shape[0] <= 1, f"Found more than one type hint for {ident}"
            hint = hinted[TraceData.VARTYPE].values[0].__name__

            hinted_targets.append(
                cst.AnnAssign(
                    target=cst.Name(value=ident),
                    annotation=cst.Annotation(cst.Name(value=hint)),
                    value=None,
                )
            )

        hinted_targets.append(original_node)
        return cst.FlattenSentinel(hinted_targets)

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.BaseSmallStatement | cst.FlattenSentinel[cst.BaseSmallStatement]:
        targets = self._find_targets(original_node)
        target_idents = list(map(operator.itemgetter(0), targets))

        logger.debug(f"Applying hints to '{target_idents} for an AugAssign'")

        cdef = self._outermost_class()
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
            self.df[TraceData.LINENO] == pos.line,
            class_check,
        ]

        local_vars = self.df[functools.reduce(operator.and_, var_mask_local_variables)]
        class_members = self.df[functools.reduce(operator.and_, var_mask_class_members)]

        if len(targets) > 1:
            hinted_targets: list[cst.BaseSmallStatement] = []
            for ident, var in targets:
                if isinstance(var, cst.Name):
                    hinted = local_vars[TraceData.VARNAME] == ident
                else:
                    hinted = class_members[TraceData.VARNAME] == ident

                assert (
                    hinted.shape[0] <= 1
                ), f"Found more than one type hint for {ident}"
                hint = hinted[TraceData.VARTYPE].values[0].__name__

                hinted_targets.append(
                    cst.AnnAssign(
                        target=cst.Name(value=ident),
                        annotation=cst.Annotation(cst.Name(value=hint)),
                        value=None,
                    )
                )

            hinted_targets.append(original_node)
            return cst.FlattenSentinel(hinted_targets)

        if isinstance(var, cst.Name):
            hinted = local_vars[TraceData.VARNAME] == target_idents[0]
        else:
            hinted = class_members[TraceData.VARNAME] == target_idents[0]

        assert (
            hinted.shape[0] <= 1
        ), f"Found more than one type hint for {target_idents[0]}"
        hint = hinted[TraceData.VARTYPE].values[0].__name__
        return updated_node.with_changes(annotation=cst.Annotation(cst.Name(hint)))

class InlineGenerator(TypeHintGenerator):
    ident = "inline"

    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, nodes: cst.Module
    ) -> cst.Module:
        visitor = TypeHintTransformer(applicable)
        nodes.visit(visitor)

        return nodes

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Inline means overwriting the original
        contents = hinting.code
        with source_file.open("w") as f:
            f.write(contents)
