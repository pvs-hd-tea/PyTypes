import libcst as cst
import pathlib
from constants import Schema
from common import TraceDataCategory
from typegen import StubFileGenerator
from typegen.strats.gen import TypeHintGenerator
from tests.typegen.strats._sample_data import get_test_data
import pandas as pd

def load_cst_module(path: pathlib.Path) -> cst.Module:
    module = cst.parse_module(source=path.open().read())
    return module


def test_factory():
    gen = TypeHintGenerator(ident=StubFileGenerator.ident, types=pd.DataFrame())
    assert isinstance(
        gen, StubFileGenerator
    ), f"{type(gen)} should be {StubFileGenerator.__name__}"


def test_stub_file_generator_generates_expected_content(get_test_data):
    for test_element in get_test_data:
        resource_path = test_element[0]
        sample_trace_data = test_element[1]
        expected_stub_file_content = test_element[4]
        assert resource_path.is_file()

        gen = TypeHintGenerator(ident=StubFileGenerator.ident, types=pd.DataFrame())
        hinted = gen._gen_hinted_ast(
            applicable=sample_trace_data, module=load_cst_module(resource_path)
        )
        absolute_resource_path = pathlib.Path.cwd() / resource_path
        gen._store_hinted_ast(absolute_resource_path, hinted)

        expected_stub_file_path = resource_path.with_suffix(".pyi")
        assert expected_stub_file_path.is_file()
        with expected_stub_file_path.open() as stub_file:
            actual_stub_file_content = stub_file.read()
        expected_stub_file_path.unlink()
        if actual_stub_file_content != expected_stub_file_content:
            print(f"Test failed for: {str(resource_path)}")
            print("Expected generated code: ")
            print("---")
            print(expected_stub_file_content)
            print("---")
            print("Actual generated code: ")
            print("---")
            print(actual_stub_file_content)
            print("---")
            assert False


def test_stub_file_generator_generates_file_with_correct_content_with_union_import():
    resource_path = pathlib.Path("tests", "resource", "typegen", "sample_file_with_type_hint_unions.py")
    empty_trace_data = pd.DataFrame(columns=Schema.TraceData)

    empty_trace_data.loc[len(empty_trace_data.index)] = [
        "",
        None,
        None,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        None,
        None,
        None,
    ]

    gen = TypeHintGenerator(ident=StubFileGenerator.ident, types=empty_trace_data)
    hinted = gen._gen_hinted_ast(
        applicable=empty_trace_data, module=load_cst_module(resource_path)
    )
    absolute_resource_path = pathlib.Path.cwd() / resource_path
    gen._store_hinted_ast(absolute_resource_path, hinted)

    expected_stub_file_content = """from typing import Union
def function(parameter: Union[int, None]) -> Union[str, int]: ...
"""
    expected_stub_file_path = resource_path.with_suffix(".pyi")
    assert expected_stub_file_path.is_file()
    with expected_stub_file_path.open() as stub_file:
        actual_stub_file_content = stub_file.read()
    assert actual_stub_file_content == expected_stub_file_content
    expected_stub_file_path.unlink()


def test_stub_file_generator_generates_file_with_correct_content_with_custom_union_without_union_import():
    resource_path = pathlib.Path("tests", "resource", "typegen", "sample_file_with_custom_union.py")
    empty_trace_data = pd.DataFrame(columns=Schema.TraceData)

    empty_trace_data.loc[len(empty_trace_data.index)] = [
        "",
        None,
        None,
        "",
        0,
        TraceDataCategory.CLASS_MEMBER,
        None,
        None,
        None,
    ]

    gen = TypeHintGenerator(ident=StubFileGenerator.ident, types=empty_trace_data)
    hinted = gen._gen_hinted_ast(
        applicable=empty_trace_data, module=load_cst_module(resource_path)
    )
    absolute_resource_path = pathlib.Path.cwd() / resource_path
    gen._store_hinted_ast(absolute_resource_path, hinted)

    expected_stub_file_content = """class Union: ...

def function(parameter: int) -> Union: ...
"""
    expected_stub_file_path = resource_path.with_suffix(".pyi")
    assert expected_stub_file_path.is_file()
    with expected_stub_file_path.open() as stub_file:
        actual_stub_file_content = stub_file.read()
    assert actual_stub_file_content == expected_stub_file_content
    expected_stub_file_path.unlink()


