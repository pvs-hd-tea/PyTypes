import ast
import pathlib

import constants

from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import Generator
from typegen.strats.inline import InlineGenerator


import pandas as pd


def test_factory():
    gen = Generator(ident=InlineGenerator.ident, types=pd.DataFrame())
    assert isinstance(
        gen, InlineGenerator
    ), f"{type(gen)} should be {InlineGenerator.__name__}"


def test_callables():
    resource_path = pathlib.Path("tests", "resource", "typegen", "callable.py")
    assert resource_path.is_file()

    # Workaround for getting the class
    from tests.resource.typegen.callable import C # type: ignore

    c_clazz = C

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "x",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "y",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "add",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        5,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "n",
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        5,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "s",
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "method",
        "bytes",
    ]

    print(traced.head())

    gen = Generator(ident=InlineGenerator.ident, types=traced)
    hinted = gen._gen_hints(
        applicable=traced, nodes=ast.parse(source=resource_path.open().read())
    )

    print(ast.unparse(hinted))
    assert False


    class HintTest(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            return super().visit_FunctionDef(node)
