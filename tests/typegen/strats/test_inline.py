import ast
import logging
import pathlib
from types import NoneType

import constants
import typing

from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.inline import InlineGenerator


import pandas as pd


class HintTest(ast.NodeVisitor):
    @typing.no_type_check
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == "add":
            for arg in node.args.args:
                assert arg.annotation.id == "int", f"{ast.dump(arg)}"
            assert node.returns.id == "int", f"{ast.dump(node)}"

        elif node.name == "method":
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

        elif node.name == "__init__":
            pass

        elif node.name == "outer":
            assert node.args.args[1].arg == "b"
            assert node.args.args[1].annotation.id == "int"
            assert node.returns.id == "int"

        elif node.name == "inner":
            assert node.args.args[0].arg == "i"
            assert node.args.args[0].annotation.id == "int"
            assert node.returns.id == "int"

        else:
            assert False, f"Unhandled target: {ast.dump(node)}"

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # narrow type for mypy
        assert isinstance(node.target, ast.Name) or isinstance(
            node.target, ast.Attribute
        )
        assert isinstance(node.annotation, ast.Name)

        if node.value is not None:
            if isinstance(node.target, ast.Name):
                if node.target.id == "z":
                    assert node.annotation.id == "int"
                elif node.target.id == "y":
                    assert node.annotation.id == "float"
                elif node.target.id == "d":
                    assert node.annotation.id == "dict"
                elif node.target.id == "s":
                    assert node.annotation.id == "set"
                elif node.target.id == "l":
                    assert node.annotation.id == "list"
                elif node.target.id == "f":
                    assert node.annotation.id == "int"
                else:
                    assert False, f"Unhandled ann-assign with target: {ast.dump(node)}"
            elif isinstance(node.target, ast.Attribute):
                if node.target.attr == "a":
                    assert node.annotation.id == "int"
                elif node.target.attr == "b":
                    assert node.annotation.id == "str"
                else:
                    assert False, f"Unhandled ann-assign with target: {ast.dump(node)}"
        else:
            if isinstance(node.target, ast.Name):
                if node.target.id == "a":
                    assert node.annotation.id == "float"
                elif node.target.id == "b":
                    assert node.annotation.id == "int"
                elif node.target.id == "i":
                    assert node.annotation.id == "float"
                elif node.target.id == "j":
                    assert node.annotation.id == "int"
                elif node.target.id == "f":
                    assert node.annotation.id == "int"
                elif node.target.id == "y":
                    assert node.annotation.id == "int"
                elif node.target.id == "d":
                    assert node.annotation.id == "float"
                elif node.target.id == "e":
                    assert node.annotation.id == "NoneType"
                else:
                    assert (
                        False
                    ), f"Unhandled ann-assign without target: {ast.dump(node)}"
            elif isinstance(node.target, ast.Attribute):
                if node.target.attr == "a":
                    assert node.annotation.id == "int"
                elif node.target.attr == "b":
                    assert node.annotation.id == "str"
                elif node.target.attr == "c":
                    assert node.annotation.id == "bool"
                else:
                    assert False, f"Unhandled ann-assign with target: {ast.dump(node)}"

def test_factory():
    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    assert isinstance(
        gen, InlineGenerator
    ), f"{type(gen)} should be {InlineGenerator.__name__}"


def test_callables():
    resource_path = pathlib.Path("tests", "resource", "typegen", "callable.py")
    assert resource_path.is_file()

    from tests.resource.typegen.callable import C
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
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "a",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "b",
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "c",
        "bool",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "n",
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "s",
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        10,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        "float",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        11,
        TraceDataCategory.LOCAL_VARIABLE,
        "e",
        "NoneType",
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

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "outer",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "outer",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "outer",
        15,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "b",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "inner",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        16,
        TraceDataCategory.FUNCTION_ARGUMENT,
        "i",
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "a",
        "int",
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=traced)
    hinted = gen._gen_hinted_ast(
        applicable=traced, nodes=ast.parse(source=resource_path.open().read())
    )

    logging.debug(f"\n{ast.unparse(hinted)}")

    for node in ast.walk(hinted):
        HintTest().visit(node)


def test_assignments():
    resource_path = pathlib.Path("tests", "resource", "typegen", "assignments.py")
    assert resource_path.is_file()

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "z",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        7,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        "dict",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        8,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        "set",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        9,
        TraceDataCategory.LOCAL_VARIABLE,
        "l",
        "list",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "a",
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "b",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "i",
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "j",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        "int",
    ]

    hinted = gen._gen_hinted_ast(
        applicable=traced, nodes=ast.parse(source=resource_path.open().read())
    )
    logging.debug(ast.unparse(hinted))

    for node in ast.walk(hinted):
        HintTest().visit(node)
