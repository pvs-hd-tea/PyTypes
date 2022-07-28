import ast
import logging
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

    c_clazz = "C"

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

    gen = Generator(ident=InlineGenerator.ident, types=traced)
    hinted = gen._gen_hints(
        applicable=traced, nodes=ast.parse(source=resource_path.open().read())
    )

    logging.debug(f"\n{ast.unparse(hinted)}")

    class HintTest(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            if node.name == "add":
                for arg in node.args.args:
                    assert arg.annotation.id == "int", f"{ast.dump(arg)}"
                assert node.returns.id == "int", f"{ast.dump(node)}"

            if node.name == "method":
                # only the function
                if all(arg.arg in "ans" for arg in node.args.args):
                    for arg in node.args.args:
                        if arg.arg == "a":
                            assert arg.annotation is None
                        else:
                            assert arg.annotation.id == "str", f"{ast.dump(arg)}"

                    assert node.returns.id == "bytes", f"{ast.dump(node)}"
                else:
                    for arg in node.args.args:
                        assert arg.annotation is None, f"{ast.dump(arg)}"

    for node in ast.walk(hinted):
        HintTest().visit(node)