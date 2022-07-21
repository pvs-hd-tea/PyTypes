import ast
import pathlib
import itertools

from constants import TraceData
from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import Generator

import pandas as pd


# It is important to handle sub-nodes from their parent node, as line numbering may differ across multi line statements
class TypeHintApplierVisitor(ast.NodeTransformer):
    def __init__(self, relevant: pd.DataFrame) -> None:
        super().__init__()
        self.df = relevant

    def visit_FunctionDef(self, fdef: ast.FunctionDef):
        # NOTE: disregards *args (fdef.vararg) and **kwargs (fdef.kwarg)

        # parameters
        params = self.df[
            (self.df[TraceData.CATEGORY == TraceDataCategory.FUNCTION_ARGUMENT])
            & (self.df[TraceData.FUNCNAME == fdef.name])
        ]

        for arg in itertools.chain(fdef.args.posonlyargs, fdef.args.args):
            # Narrow by line number and identifier
            arg_hint = params[
                (params[TraceData.LINENO] == arg.lineno)
                & (params[TraceData.VARNAME] == arg.arg)
            ]

            # no type hint, skip
            if arg_hint.shape[0] == 0:
                continue

            assert arg_hint.shape[0] == 1
            arg.type_comment = arg_hint[TraceData.VARTYPE].values[0]

        # return type
        rettypes = self.df[
            (self.df[TraceData.CATEGORY == TraceDataCategory.FUNCTION_RETURN])
            & (self.df[TraceData.VARNAME == fdef.name])
            & (self.df[TraceData.LINENO] == arg.lineno)
        ]

        # no type hint, skip
        if arg_hint.shape[0] == 0:
            return
        assert arg_hint.shape[0] == 1
        fdef.returns.type_comment = rettypes[TraceData.VARTYPE].values[0]


class InlineGenerator(Generator):
    ident = "inline"

    def _gen_hints(self, path: pathlib.Path) -> ast.AST:
        # Get type hints relevant to this file
        applicable = self.types[self.types[TraceData.FILENAME] == str(path)]

        nodes = ast.parse(path.open().read())
        visitor = TypeHintApplierVisitor(applicable)

        # Out of order traversal, non recursive
        for node in ast.walk(nodes):
            visitor.visit(node)
        return nodes

    def _store_hints(self, source_file: pathlib.Path, hinting: ast.AST) -> None:
        # Inline means overwriting the original
        contents = ast.unparse(hinting)
        with source_file.open("w") as f:
            f.write(contents)
