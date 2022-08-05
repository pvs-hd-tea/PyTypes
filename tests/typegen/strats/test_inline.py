import libcst as cst
from libcst.tool import dump
import logging
import pathlib
from types import NoneType

import constants
import typing

from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.inline import InlineGenerator

import pandas as pd


class HintTest(cst.CSTVisitor):
    @typing.no_type_check
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        if node.name.value == "add":
            for param in node.params.params:
                assert (
                    param.annotation is not None
                ), f"Missing annotation on {dump(param)}"
                assert (
                    param.annotation.annotation.value == "int"
                ), f"Wrong annotation on {dump(param)}"

            assert (
                node.returns is not None
            ), f"Missing return annotation on {dump(node)}"
            assert node.returns.annotation.value == "int", f"{dump(node)}"

        elif node.name.value == "method":
            # only the function
            if all(param.name.value in "ans" for param in node.params.params):
                for param in node.params.params:
                    if param.name.value == "a":
                        assert param.annotation is None
                    else:
                        assert (
                            param.annotation.annotation.value == "str"
                        ), f"{dump(param)}"

                assert (
                    node.returns is not None
                ), f"Missing return annotation on {dump(node)}"
                assert (
                    node.returns.annotation.value == "bytes"
                ), f"{dump(node)}"
            else:
                for param in node.params.params:
                    assert (
                        param.annotation is None
                    ), f"{dump(param)} should not be hinted"

        elif node.name.value == "__init__":
            pass

        elif node.name.value == "outer":
            assert node.params.params[1].name.value == "b"
            assert node.params.params[1].annotation.annotation.value == "int"
            assert node.returns.annotation.value == "int"

        elif node.name.value == "inner":
            assert node.params.params[0].name.value == "i"
            assert node.params.params[0].annotation.annotation.value == "int"
            assert node.returns.annotation.value == "int"

        else:
            assert False, f"Unhandled target: {dump(node)}"

    @typing.no_type_check
    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        # narrow type for mypy
        assert isinstance(node.target, cst.Name) or isinstance(
            node.target, cst.Attribute
        )
        assert isinstance(node.annotation, cst.Annotation)

        if node.value is not None:
            if isinstance(node.target, cst.Name):
                if node.target.value == "z":
                    assert node.annotation.annotation.value == "int"
                elif node.target.value == "y":
                    assert node.annotation.annotation.value == "float"
                elif node.target.value == "d":
                    assert node.annotation.annotation.value == "dict"
                elif node.target.value == "s":
                    assert node.annotation.annotation.value == "set"
                elif node.target.value == "l":
                    assert node.annotation.annotation.value == "list"
                elif node.target.value == "f":
                    assert node.annotation.annotation.value == "int"
                else:
                    assert False, f"Unhandled ann-assign with target: {dump(node)}"
            elif isinstance(node.target, cst.Attribute):
                if node.target.attr.value == "a":
                    assert node.annotation.annotation.value == "int"
                elif node.target.attr.value == "b":
                    assert node.annotation.annotation.value == "str"
                else:
                    assert False, f"Unhandled ann-assign with target: {dump(node)}"
        else:
            if isinstance(node.target, cst.Name):
                if node.target.value == "a":
                    assert node.annotation.annotation.value == "float"
                elif node.target.value == "b":
                    assert node.annotation.annotation.value == "int"
                elif node.target.value == "i":
                    assert node.annotation.annotation.value == "float"
                elif node.target.value == "j":
                    assert node.annotation.annotation.value == "int"
                elif node.target.value == "f":
                    assert node.annotation.annotation.value == "int"
                elif node.target.value == "y":
                    assert node.annotation.annotation.value == "int"
                elif node.target.value == "d":
                    assert node.annotation.annotation.value == "float"
                elif node.target.value == "e":
                    assert node.annotation.annotation.value == "NoneType"
                else:
                    assert False, f"Unhandled ann-assign without target: {dump(node)}"
            elif isinstance(node.target, cst.Attribute):
                if node.target.attr.value == "a":
                    assert node.annotation.annotation.value == "int"
                elif node.target.attr.value == "b":
                    assert node.annotation.annotation.value == "str"
                elif node.target.attr.value == "c":
                    assert node.annotation.annotation.value == "bool"
                else:
                    assert False, f"Unhandled ann-assign with target: {dump(node)}"


def load_with_metadata(path: pathlib.Path) -> cst.MetadataWrapper:
    module = cst.parse_module(source=path.open().read())
    module_w_metadata = cst.MetadataWrapper(module)

    return module_w_metadata


def test_factory():
    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    assert isinstance(
        gen, InlineGenerator
    ), f"{type(gen)} should be {InlineGenerator.__name__}"


def test_callables():
    resource_path = pathlib.Path("tests", "resource", "typegen", "callable.py")
    assert resource_path.is_file()

    from tests.resource.typegen.callable import C  # type: ignore

    c_clazz = C

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "x",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "y",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        "add",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "add",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "a",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "b",
        str,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "c",
        bool,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_PARAMETER,
        "n",
        str,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_PARAMETER,
        "s",
        str,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        10,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        float,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "",
        11,
        TraceDataCategory.LOCAL_VARIABLE,
        "e",
        NoneType,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "method",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "method",
        bytes,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "outer",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "outer",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "outer",
        15,
        TraceDataCategory.FUNCTION_PARAMETER,
        "b",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "inner",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        16,
        TraceDataCategory.FUNCTION_PARAMETER,
        "i",
        int,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz,
        "inner",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "a",
        int,
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=traced)
    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )

    logging.debug(f"\n{hinted.code}")
    hinted.visit(HintTest())


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
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        float,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        7,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        dict,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        8,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        set,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        9,
        TraceDataCategory.LOCAL_VARIABLE,
        "l",
        list,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "a",
        float,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "b",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "i",
        float,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "j",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        int,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        int,
    ]

    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    logging.debug(f"\n{hinted.code}")
    hinted.visit(HintTest())
