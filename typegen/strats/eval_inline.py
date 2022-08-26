from typegen.strats.imports import AddImportTransformer
from .inline import InlineGenerator, TypeHintTransformer
import pandas as pd
import libcst as cst


class RemoveAllTypeHintsTransformer(cst.CSTTransformer):
    """Transforms the CST by removing all type hints."""

    def leave_FunctionDef(
        self, _: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        return updated_node.with_changes(returns=None)

    def leave_Param(self, _: cst.Param, updated_node: cst.Param) -> cst.Param:
        return updated_node.with_changes(annotation=None)

    def leave_AnnAssign(
        self, original_node: cst.AnnAssign, _: cst.AnnAssign
    ) -> cst.Assign | cst.AnnAssign | cst.RemovalSentinel:
        if original_node.value is None:
            return cst.RemoveFromParent()

        return cst.Assign(
            targets=[cst.AssignTarget(original_node.target)],
            value=original_node.value,
        )


class EvaluationInlineGenerator(InlineGenerator):
    ident = "eval_inline"

    def _transformers(
        self, module_path: str, applicable: pd.DataFrame
    ) -> list[cst.CSTTransformer]:
        return [
            RemoveAllTypeHintsTransformer(),
            TypeHintTransformer(module_path, applicable),
            AddImportTransformer(applicable),
        ]
