import libcst as cst
from libcst.tool import dump
from libcst.matchers import matches
import logging
import pathlib

import constants
import typing

from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.inline import InlineGenerator

import pandas as pd


class HintTest(cst.CSTVisitor):
    @typing.no_type_check
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        assert False, "no imports expected!"

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
                assert node.returns.annotation.value == "bytes", f"{dump(node)}"
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

    c_clazz_module = "tests.resource.typegen.callable"
    c_clazz = "C"

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "x",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "add",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "y",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "add",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "add",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "a",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "b",
        None,
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "c",
        None,
        "bool",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_PARAMETER,
        "n",
        None,
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "method",
        8,
        TraceDataCategory.FUNCTION_PARAMETER,
        "s",
        None,
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "",
        10,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        None,
        "float",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "",
        11,
        TraceDataCategory.LOCAL_VARIABLE,
        "e",
        None,
        "NoneType",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "method",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "method",
        None,
        "bytes",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "outer",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "outer",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "outer",
        15,
        TraceDataCategory.FUNCTION_PARAMETER,
        "b",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "inner",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "inner",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        c_clazz_module,
        c_clazz,
        "inner",
        16,
        TraceDataCategory.FUNCTION_PARAMETER,
        "i",
        None,
        "int",
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=traced)
    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")
    imported.visit(HintTest())


def test_assignments():
    resource_path = pathlib.Path("tests", "resource", "typegen", "assignments.py")
    assert resource_path.is_file()

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        2,
        TraceDataCategory.LOCAL_VARIABLE,
        "z",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        4,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        None,
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        7,
        TraceDataCategory.LOCAL_VARIABLE,
        "d",
        None,
        "dict",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        8,
        TraceDataCategory.LOCAL_VARIABLE,
        "s",
        None,
        "set",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        9,
        TraceDataCategory.LOCAL_VARIABLE,
        "l",
        None,
        "list",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "a",
        None,
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "b",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "i",
        None,
        "float",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "j",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        18,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        20,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "f",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        21,
        TraceDataCategory.LOCAL_VARIABLE,
        "y",
        None,
        "int",
    ]

    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")
    imported.visit(HintTest())


def test_imported():
    resource_path = pathlib.Path("tests", "resource", "typegen", "importing.py")
    assert resource_path.is_file()

    c_clazz_module = "tests.resource.typegen.callable"
    c_clazz = "C"

    anotherc_clazz_module = "tests.resource.typegen.importing"
    anotherc_clazz = "AnotherC"

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "function",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "function",
        None,
        "int",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "function",
        1,
        TraceDataCategory.FUNCTION_PARAMETER,
        "c",
        c_clazz_module,
        c_clazz,
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "another_function",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "another_function",
        None,
        "str",
    ]

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "another_function",
        7,
        TraceDataCategory.FUNCTION_PARAMETER,
        "c",
        anotherc_clazz_module,
        anotherc_clazz,
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")

    class ImportedHintTest(cst.CSTVisitor):
        @typing.no_type_check
        def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
            if matches(node.module, cst.parse_expression("__future__")):
                assert isinstance(node.module, cst.Name)
                assert len(node.names) == 1
                assert node.names[0].name.value == "annotations"

            elif matches(node.module, cst.parse_expression("typing")):
                assert isinstance(node.module, cst.Name)
                assert len(node.names) == 1
                assert node.names[0].name.value == "TYPE_CHECKING"

            elif matches(
                node.module, cst.parse_expression("tests.resource.typegen.callable")
            ):
                assert isinstance(node.module, cst.Attribute)
                assert len(node.names) == 1
                assert node.names[0].name.value == "C"

            else:
                assert False, f"Unexpected ImportFrom: {node.module.value}"

        @typing.no_type_check
        def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
            if node.name.value == "function":
                assert node.params.params[0].name.value == "c"
                assert node.params.params[0].annotation.annotation.value == "C"

                assert node.returns.annotation.value == "int"

            elif node.name.value == "another_function":
                assert node.params.params[0].name.value == "c"
                assert node.params.params[0].annotation.annotation.value == "AnotherC"

                assert node.returns.annotation.value == "str"

            else:
                assert False, f"Unhandled functiondef: {node.name.value}"

    imported.visit(ImportedHintTest())


def test_present_annotations_are_removed():
    # Nothing was gathered that is in the file
    resource_path = pathlib.Path("tests", "resource", "typegen", "pretyped.py")
    assert resource_path.is_file()

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        -1,
        TraceDataCategory.FUNCTION_RETURN,
        "",
        None,
        "",
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)

    class HintLessTest(cst.CSTVisitor):
        def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
            # arguments
            assert all(param.annotation is None for param in node.params.params)
            # return
            assert node.returns is None
            return True

        def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
            # no annotations
            assert False, f"Type hint should not have been set: {dump(node)}"

        def visit_Assign(self, node: cst.Assign) -> bool | None:
            # cannot be annotated, trivially true
            return True

    logging.debug(f"{imported.code}")
    imported.visit(HintLessTest())


def test_attributes_are_not_annotated_outside_of_classes():
    resource_path = pathlib.Path("tests", "resource", "typegen", "attribute.py")
    class_module = "tests.resource.typegen.attribute"
    class_name1 = "AClass"
    class_name2 = "AnotherC"

    traced = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name1,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "aclass_attr",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name2,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        "ano_attr",
        class_module,
        class_name1,
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, hintless_ast=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")

    class ExternalAttributesAreHintLessVisitor(cst.CSTVisitor):
        def __init__(self) -> None:
            self.classes: list[cst.ClassDef] = list()

        def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
            self.classes.append(node)
            return True

        def leave_ClassDef(self, _: cst.ClassDef) -> None:
            self.classes.pop()

        def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
            if isinstance(node.target, cst.Attribute):
                assert (
                    self.classes
                ), f"Found annotated assignment for attribute outside of class!: {dump(node)}"

            return True

    imported.visit(ExternalAttributesAreHintLessVisitor())
