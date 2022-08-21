import libcst as cst
import pathlib
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.inline import InlineGenerator
from tests.typegen.strats._sample_data import get_test_data
import pandas as pd


def load_with_metadata(path: pathlib.Path) -> cst.MetadataWrapper:
    module = cst.parse_module(source=path.open().read())
    module_w_metadata = cst.MetadataWrapper(module)

    return module_w_metadata


def test_factory():
    gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
    assert (
        type(gen) is InlineGenerator
    ), f"{type(gen)} should be {InlineGenerator.__name__}"


def test_inline_generator_generates_expected_content(get_test_data):
    for test_element in get_test_data:
        resource_path = test_element[0]
        sample_trace_data = test_element[1]
        expected_inline_content = test_element[2]
        assert resource_path.is_file()

        gen = TypeHintGenerator(ident=InlineGenerator.ident, types=pd.DataFrame())
        hinted = gen._gen_hinted_ast(
            applicable=sample_trace_data, ast_with_metadata=load_with_metadata(resource_path)
        )
        imported = gen._add_all_imports(applicable=sample_trace_data, hinted_ast=hinted)
        actual_file_content = imported.code
        if actual_file_content != expected_inline_content:
            print(f"Test failed for: {str(resource_path)}")
            print("Expected generated code: ")
            print("---")
            print(expected_inline_content)
            print("---")
            print("Actual generated code: ")
            print("---")
            print(actual_file_content)
            print("---")
            assert False

