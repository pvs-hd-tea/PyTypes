import ast
import pathlib

import constants
from typegen.strats.gen import Generator

import pandas as pd


class TypeHintApplierVisitor(ast.NodeTransformer):
    def __init__(self, relevant: pd.DataFrame) -> None:
        super().__init__()
        self.df = relevant


class InlineGenerator(Generator):
    ident = "inline"

    def _apply(self, path: pathlib.Path) -> None:
        applicable = self.types[self.types[constants.TraceData.FILENAME] == str(path)]
        
        nodes = ast.parse(path.open().read())
        visitor = TypeHintApplierVisitor(applicable)

        for node in ast.walk(nodes):
            visitor.visit(node)

        serialized = ast.unparse(nodes)
        with path.open("w") as f:
            f.write(serialized)