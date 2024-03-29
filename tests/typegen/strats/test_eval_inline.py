import libcst as cst
import pathlib
from typegen.strats.gen import TypeHintGenerator
from typegen.strats.eval_inline import EvaluationInlineGenerator
from tests.typegen.strats._sample_data import get_test_data
import pandas as pd


def load_cst_module(path: pathlib.Path) -> cst.Module:
    module = cst.parse_module(source=path.open().read())
    return module


def test_factory():
    gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
    assert (
        type(gen) is EvaluationInlineGenerator
    ), f"{type(gen)} should be {EvaluationInlineGenerator.__name__}"


def test_inline_generator_generates_expected_content(get_test_data):
    for test_element in get_test_data:
        resource_path = test_element[0]
        sample_trace_data = test_element[1]
        expected_eval_inline_content = test_element[3]
        assert resource_path.is_file()

        print(f"Working on {resource_path}")

        gen = TypeHintGenerator(ident=EvaluationInlineGenerator.ident, types=pd.DataFrame())
        hinted = gen._gen_hinted_ast(
            applicable=sample_trace_data, module=load_cst_module(resource_path)
        )
        actual_file_content = hinted.code
        if actual_file_content != expected_eval_inline_content:
            print(f"Test failed for: {str(resource_path)}")
            print("Expected generated code: ")
            print("---")
            print(expected_eval_inline_content)
            print("---")
            print("Actual generated code: ")
            print("---")
            print(actual_file_content)
            print("---")
            assert False

