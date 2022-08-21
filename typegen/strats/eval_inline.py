from .inline import InlineGenerator, TypeHintTransformer
import os
import pandas as pd
import libcst as cst
from constants import Column


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

    def _gen_hinted_ast(
        self, applicable: pd.DataFrame, ast_with_metadata: cst.MetadataWrapper
    ) -> cst.Module:
        # Access is safe, as check in base class guarantees at least one element
        filename = applicable[Column.FILENAME].values[0]
        assert filename is not None

        path = os.path.splitext(filename)[0]
        as_module = path.replace(os.path.sep, ".")

        remove_hints_transformer = RemoveAllTypeHintsTransformer()
        hintless_ast = ast_with_metadata.visit(remove_hints_transformer)

        hintless_ast_with_metadata = cst.MetadataWrapper(hintless_ast)
        typehint_transformer = TypeHintTransformer(as_module, applicable)
        hinted = hintless_ast_with_metadata.visit(typehint_transformer)

        return hinted