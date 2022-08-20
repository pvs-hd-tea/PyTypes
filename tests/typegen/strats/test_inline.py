import libcst as cst
from libcst.tool import dump
from libcst.matchers import matches
import libcst.matchers as m
import logging
import pathlib

from constants import Schema
import typing

from tracing.trace_data_category import TraceDataCategory
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.inline import InlineGenerator, EvaluationInlineGenerator

from typegen.unification.union import TraceDataFilter, UnionFilter

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
                    # corner case: NoneType is replaced by None
                    assert node.annotation.annotation.value == "None"
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
    assert (
        type(gen) is InlineGenerator
    ), f"{type(gen)} should be {InlineGenerator.__name__}"

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    assert (
        type(gen) is EvaluationInlineGenerator
    ), f"{type(gen)} should be {EvaluationInlineGenerator.__name__}"


def test_callables():
    resource_path = pathlib.Path("tests", "resource", "typegen", "callable.py")
    assert resource_path.is_file()

    c_clazz_module = "tests.resource.typegen.callable"
    c_clazz = "C"

    traced = pd.DataFrame(columns=Schema.TraceData.keys())
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
        None,
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
        None,
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
        None,
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
        None,
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
        None,
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

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=traced)
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")
    imported.visit(HintTest())


def test_assignments():
    resource_path = pathlib.Path("tests", "resource", "typegen", "assignments.py")
    assert resource_path.is_file()

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())

    traced = pd.DataFrame(columns=Schema.TraceData.keys())

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
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
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

    traced = pd.DataFrame(columns=Schema.TraceData.keys())

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

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
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

    traced = pd.DataFrame(columns=Schema.TraceData.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        -1,
        TraceDataCategory.FUNCTION_RETURN,
        None,
        None,
        "",
    ]

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
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


def test_inline_and_evaluation_in_line_generator_generate_file_correctly():
    resource_path = pathlib.Path(
        "tests", "resource", "typegen", "file_with_existing_type_hints.py"
    )
    expected_generated_evaluation_inline_code = """class Clazz:
    def __init__(self):
        self.class_member: int = 5

    def change_value(self, parameter1: str, parameter2: str) -> bool:
        local_variable = parameter1 == parameter2
        self.class_member: int = int(local_variable)
        return local_variable


def function(parameter: Clazz):
    assert isinstance(parameter, Clazz)
"""

    expected_generated_inline_code = """class Clazz:
    def __init__(self):
        self.class_member: int = 5

    def change_value(self, parameter1: int, parameter2: str) -> bool:
        local_variable = parameter1 == parameter2
        self.class_member: int = int(local_variable)
        return local_variable


def function(parameter: Clazz):
    assert isinstance(parameter, Clazz)
"""

    traced = pd.DataFrame(columns=Schema.TraceData.keys())
    class_module = "tests.resource.typegen.file_with_existing_type_hints"
    class_name = "Clazz"
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name,
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "class_member",
        None,
        "int",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name,
        "change_value",
        5,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter1",
        None,
        "str",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name,
        "change_value",
        5,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter2",
        None,
        "str",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name,
        "change_value",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "change_value",
        None,
        "bool",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name,
        "function",
        11,
        TraceDataCategory.FUNCTION_PARAMETER,
        "parameter",
        class_module,
        class_name,
    ]

    evaluation_inline_gen = TypeHintGenerator(
        ident=EvaluationInlineGenerator.ident, types=traced
    )
    hinted = evaluation_inline_gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
    )
    imported = evaluation_inline_gen._add_all_imports(
        applicable=traced, hinted_ast=hinted
    )
    assert imported.code == expected_generated_evaluation_inline_code

    evaluation_inline_gen = TypeHintGenerator(ident=InlineGenerator.ident, types=traced)
    hinted = evaluation_inline_gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
    )
    imported = evaluation_inline_gen._add_all_imports(
        applicable=traced, hinted_ast=hinted
    )
    assert imported.code == expected_generated_inline_code


def test_attributes_are_not_annotated_outside_of_classes():
    resource_path = pathlib.Path("tests", "resource", "typegen", "attribute.py")
    class_module = "tests.resource.typegen.attribute"
    class_name1 = "AClass"
    class_name2 = "AnotherC"

    traced = pd.DataFrame(columns=Schema.TraceData.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        class_module,
        class_name1,
        None,
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
        None,
        0,
        TraceDataCategory.CLASS_MEMBER,
        "ano_attr",
        class_module,
        class_name1,
    ]

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
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


def test_union_import_generation():
    resource_path = pathlib.Path("tests", "resource", "typegen", "unions.py")

    traced = pd.DataFrame(columns=Schema.TraceData.keys())
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "stringify",
        4,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        ",,pathlib",
        f"{int.__name__} | {str.__name__} | {pathlib.Path.__name__}",
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "stringify",
        0,
        TraceDataCategory.FUNCTION_RETURN,
        "stringify",
        None,
        str.__name__,
    ]

    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"\n{imported.code}")

    class CheckUnionApplicationVisitor(cst.CSTVisitor):
        PATHLIB_IMPORT_M = m.ImportFrom(
            module=m.Name(value="pathlib"), names=[m.ImportAlias(m.Name(value="Path"))]
        )

        IF_TYPE_CHECKING_M = m.If(test=m.Name("TYPE_CHECKING"))

        def __init__(self) -> None:
            self.classes: list[cst.ClassDef] = list()
            self._in_type_matching = False

        def visit_If(self, node: cst.If) -> bool | None:
            self._in_type_matching = matches(
                node, CheckUnionApplicationVisitor.IF_TYPE_CHECKING_M
            )
            return True

        def leave_If(self, _: cst.If) -> None:
            self._in_type_matching = False

        def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
            if self._in_type_matching:
                # Only import should be from pathlib import Path
                assert matches(
                    node, CheckUnionApplicationVisitor.PATHLIB_IMPORT_M
                ), f"Did not match {dump(node)}"
            return True

    imported.visit(CheckUnionApplicationVisitor())


def test_global_hinting():
    resource_path = pathlib.Path("tests", "resource", "typegen", "glbls.py")
    traced = pd.DataFrame(columns=Schema.TraceData.keys())

    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "f",
        7,
        TraceDataCategory.LOCAL_VARIABLE,
        "not_a_global",
        None,
        str.__name__,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        "f",
        8,
        TraceDataCategory.LOCAL_VARIABLE,
        "exists_outside_of_all_scopes",
        None,
        int.__name__,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "sneaky_inside_scope",
        None,
        bool.__name__,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "sneaky_inside_scope",
        None,
        str.__name__,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "exists_outside_of_all_scopes",
        None,
        bool.__name__,
    ]
    traced.loc[len(traced.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "exists_outside_of_all_scopes",
        None,
        int.__name__,
    ]

    traced = TraceDataFilter(UnionFilter.ident).apply(traced)
    logging.debug(f"Unions:\n{traced}")

    expected_code = r"""from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass
from tracing import decorators

exists_outside_of_all_scopes: bool | int = False


def f():
    not_a_global: str = "Hello"
    exists_outside_of_all_scopes: int = 5  # This is a local variable!

    global sneaky_inside_scope
    sneaky_inside_scope: bool | str = True


def g():
    # This should induce a union type in BOTH functions
    global sneaky_inside_scope
    sneaky_inside_scope: bool | str = "TypeChange"


def h():
    # Reference existing global
    global exists_outside_of_all_scopes
    exists_outside_of_all_scopes: bool | int = 5


@decorators.trace
def main():
    # False
    print(exists_outside_of_all_scopes)
    f()

    # False True
    print(exists_outside_of_all_scopes, sneaky_inside_scope)

    # False TypeChange
    g()
    print(exists_outside_of_all_scopes, sneaky_inside_scope)

    # 5 TypeChange
    h()
    print(exists_outside_of_all_scopes, sneaky_inside_scope)


if __name__ == "__main__":
    main()
"""

    expected_ast = cst.parse_module(expected_code)

    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    hinted = gen._gen_hinted_ast(
        applicable=traced, ast_with_metadata=load_with_metadata(resource_path)
    )
    imported = gen._add_all_imports(applicable=traced, hinted_ast=hinted)
    logging.debug(f"Expected: \n{expected_ast.code}")
    logging.debug(f"Generated: \n{imported.code}")
    
    assert expected_ast.code == imported.code
    