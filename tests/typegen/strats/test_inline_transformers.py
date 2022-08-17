import libcst as cst
from typegen.strats import RemoveAllTypeHintsTransformer


def test_remove_all_hints_transformer_removes_all_hints():
    code = """class A:
    def __init__(self):
        self.a: float = 0.2

    def a(self, b: int) -> str:
        c: bool = True
        b: int
        b += 1
        e: str = "string"; f: bool = True
        return "string"
"""

    expected_code = """class A:
    def __init__(self):
        self.a = 0.2

    def a(self, b):
        c = True
        b += 1
        e = "string"; f = True
        return "string"
"""

    ast = cst.parse_module(source=code)
    test_object = RemoveAllTypeHintsTransformer()
    ast_without_hints = ast.visit(test_object)

    assert expected_code == ast_without_hints.code
