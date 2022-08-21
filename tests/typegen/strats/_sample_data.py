import pathlib

import pandas as pd
import pytest

from constants import Schema
from tracing import TraceDataCategory
from typegen import TraceDataFilter, DropDuplicatesFilter
from typegen.unification.union import UnionFilter


@pytest.fixture()
def get_test_data():
    test_data_functions = [
        get_test_data_callables,
        get_test_data_assignments,
        get_test_data_imported,
        get_test_data_pretyped,
        get_test_data_existing_type_hints,
        get_test_data_attribute,
        get_test_data_union_import,
        get_test_data_global_hinting
    ]

    returned_data = []
    for test_data_function in test_data_functions:
        (
            resource_path,
            sample_trace_data,
            expected_inline_content,
            expected_eval_inline_content,
            expected_stub_content,
        ) = test_data_function()
        returned_data.append(
            [
                resource_path,
                sample_trace_data,
                expected_inline_content,
                expected_eval_inline_content,
                expected_stub_content,
            ]
        )
    return returned_data


def get_test_data_callables():
    resource_path = pathlib.Path("tests", "resource", "typegen", "callable.py")

    c_clazz_module = "tests.resource.typegen.callable"
    c_clazz = "C"

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    expected_inline_content = """def add(x: int, y: int) -> int:
    return x + y

class C:
    def __init__(self):
        self.a: int = 0

    def method(a, n: str, s: str) -> bytes:
        a.b: str = "string"
        a.c: bool; d: float; a.c, d = True, 3.14
        a.b: str; C().a: int; e: None; e, a.b, C().a = \\
            None, "string2", 5
        return bytes(f"{n} + {s}")

    def outer(self, b: int) -> int:
        def inner(i: int) -> int:
            self.a: int; self.a += self.a + i # Can access class members anyway!
            return self.a
        return inner(b)


# Do not type hint, as it is not in the class C
def method(c, n, s):
    c.a = 5  # set attribute in class C, DO NOT TYPE HINT!
    return c.method(n, s)
"""
    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """def add(x: int, y: int) -> int: ...

class C:
    a: int
    def __init__(self) -> None: ...
    def method(a, n: str, s: str) -> bytes: ...
    def outer(self, b: int) -> int: ...

def method(c, n, s): ...
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_assignments():
    resource_path = pathlib.Path("tests", "resource", "typegen", "assignments.py")

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "z",
        None,
        "int",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "y",
        None,
        "float",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "d",
        None,
        "dict",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "s",
        None,
        "set",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "l",
        None,
        "list",
    ]

    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "a",
        None,
        "float",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "b",
        None,
        "int",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "i",
        None,
        "float",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "j",
        None,
        "int",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "f",
        None,
        "int",
    ]

    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "y",
        None,
        "int",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "f",
        None,
        "int",
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        None,
        0,
        TraceDataCategory.GLOBAL_VARIABLE,
        "y",
        None,
        "int",
    ]

    sample_trace_data = TraceDataFilter(DropDuplicatesFilter.ident).apply(sample_trace_data)
    sample_trace_data = TraceDataFilter(UnionFilter.ident).apply(sample_trace_data)

    expected_inline_content = """# Simple assignment, is lifted to AnnAssign
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass
z: int = 0
# Resulting from math op, should not differ from simple assignment
y: float | int = 5.0 + z

# data structures
d: dict = dict(zip("HelloWorld", range(10)))
s: set = set(range(10))
l: list = list(range(10))


# annotations in other chained and aug assignments are not (directly) supported 
# solution: declare variable beforehand
# a: float
# b: int
# i: float
# j: int
a: float; b: int; i: float; j: int; (a, b), (i, j) = (y, z), (y, z)

f: int; y: float | int; f = y = 10
f: int; f += y - 20
"""
    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """from typing import Union
z: int
y: Union[float, int]
d: dict
s: set
l: list
a: float
b: int
i: float
j: int
f: int
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_imported():
    resource_path = pathlib.Path("tests", "resource", "typegen", "importing.py")

    c_clazz_module = "tests.resource.typegen.callable"
    c_clazz = "C"

    anotherc_clazz_module = "tests.resource.typegen.importing"
    anotherc_clazz = "AnotherC"

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    inner_outer_module = "tests.resource.typegen.scopage"
    inner_outer_class = "OuterClass.InnerClass"
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "takes_inner_inst",
        10,
        TraceDataCategory.FUNCTION_PARAMETER,
        "inner",
        inner_outer_module,
        inner_outer_class,
    ]

    expected_inline_content = """from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.resource.typegen.callable import C
    from tests.resource.typegen.scopage import OuterClass
def function(c: C) -> int:
    return c.outer(5)

class AnotherC:
    pass

def another_function(c: AnotherC) -> str:
    return "4"

def takes_inner_inst(inner: OuterClass.InnerClass):
    return inner
"""
    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """from tests.resource.typegen.callable import C as C
from tests.resource.typegen.scopage import OuterClass as OuterClass

def function(c: C) -> int: ...

class AnotherC: ...

def another_function(c: AnotherC) -> str: ...
def takes_inner_inst(inner: OuterClass.InnerClass): ...
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_pretyped():
    resource_path = pathlib.Path("tests", "resource", "typegen", "pretyped.py")

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    expected_inline_content = """class C:
    def __init__(self) -> None:
        self.a = 5

    def m(self, i) -> int:
        return self.a + i

def f(i: int) -> str:
    c = C()
    c.a = 10
    return f"{c.m(i)}"

def another_one():
    a, b = 5, 2.0

    c = "Hello World"
"""
    expected_eval_inline_content = """class C:
    def __init__(self):
        self.a = 5

    def m(self, i):
        return self.a + i

def f(i):
    c = C()
    c.a = 10
    return f"{c.m(i)}"

def another_one():
    a, b = 5, 2.0

    c = "Hello World"
"""

    expected_stub_content = """class C:
    a: int
    def __init__(self) -> None: ...
    def m(self, i) -> int: ...

def f(i: int) -> str: ...
def another_one() -> None: ...
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_existing_type_hints():
    resource_path = pathlib.Path(
        "tests", "resource", "typegen", "file_with_existing_type_hints.py"
    )

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    class_module = "tests.resource.typegen.file_with_existing_type_hints"
    class_name = "Clazz"
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    expected_eval_inline_content = """class Clazz:
    def __init__(self):
        self.class_member: int = 5

    def change_value(self, parameter1: str, parameter2: str) -> bool:
        local_variable = parameter1 == parameter2
        self.class_member: int = int(local_variable)
        return local_variable


def function(parameter: Clazz):
    assert isinstance(parameter, Clazz)
"""

    expected_inline_content = """class Clazz:
    def __init__(self):
        self.class_member: int = 5

    def change_value(self, parameter1: int, parameter2: str) -> bool:
        local_variable = parameter1 == parameter2
        self.class_member: int = int(local_variable)
        return local_variable


def function(parameter: Clazz):
    assert isinstance(parameter, Clazz)
"""

    expected_stub_content = """class Clazz:
    class_member: int
    def __init__(self) -> None: ...
    def change_value(self, parameter1: int, parameter2: str) -> bool: ...

def function(parameter: Clazz): ...
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_attribute():
    resource_path = pathlib.Path("tests", "resource", "typegen", "attribute.py")
    class_module = "tests.resource.typegen.attribute"
    class_name1 = "AClass"
    class_name2 = "AnotherC"

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    expected_inline_content = """class AClass:
    def __init__(self, a):
        self.aclass_attr: int = a # set attribute in class C, TYPE HINT!

    def set(self, another_c):
        another_c.ano_attr = self.aclass_attr # set attribute in class C, TYPE HINT!

class AnotherC:
    def __init__(self, a):
        self.ano_attr: AClass = a # set attribute in class C, TYPE HINT!

    def reset(self, a):
        a.ano_attr: AClass = -50  # set attribute in class C, TYPE HINT!

# Do not type hint, as it is not in the class C
def func_taking_aclass(aclass):
    v, aclass.aclass_attr = 10, 5  # set attribute in class C, DO NOT TYPE HINT!
    return v

def func_taking_anotherc(anotherc):
    anotherc.ano_attr, i = 10, -20  # set attribute in class AnotherC, DO NOT TYPE HINT!
    return i


def main():
    func_taking_aclass(AClass(5))
    func_taking_anotherc(AnotherC(36))
"""

    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """from _typeshed import Incomplete

class AClass:
    aclass_attr: Incomplete
    def __init__(self, a) -> None: ...
    def set(self, another_c) -> None: ...

class AnotherC:
    ano_attr: Incomplete
    def __init__(self, a) -> None: ...
    def reset(self, a) -> None: ...

def func_taking_aclass(aclass): ...
def func_taking_anotherc(anotherc): ...
def main() -> None: ...
"""
    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )


def get_test_data_union_import():
    resource_path = pathlib.Path("tests", "resource", "typegen", "unions.py")

    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    expected_inline_content = """from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path
import pathlib


def stringify(a: int | str | Path) -> str:
    return f"{a}"


if __name__ == "__main__":
    print(stringify(1))
    print(stringify("name"))
    print(stringify(pathlib.Path.cwd()))
"""

    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """from typing import Union
from pathlib import Path

def stringify(a: Union[int, str, Path]) -> str: ...
"""

    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content,
    )

def get_test_data_global_hinting():
    resource_path = pathlib.Path("tests", "resource", "typegen", "glbls.py")
    sample_trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "f",
        5,
        TraceDataCategory.LOCAL_VARIABLE,
        "not_a_global",
        None,
        str.__name__,
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "f",
        6,
        TraceDataCategory.LOCAL_VARIABLE,
        "exists_outside_of_all_scopes",
        None,
        int.__name__,
    ]
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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
    sample_trace_data.loc[len(sample_trace_data.index)] = [
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

    sample_trace_data = TraceDataFilter(UnionFilter.ident).apply(sample_trace_data)

    expected_inline_content = r"""from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass
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

    expected_eval_inline_content = expected_inline_content

    expected_stub_content = """from typing import Union
exists_outside_of_all_scopes: Union[bool, int]

def f() -> None: ...
def g() -> None: ...
def h() -> None: ...
def main() -> None: ...
"""

    return (
        resource_path,
        sample_trace_data,
        expected_inline_content,
        expected_eval_inline_content,
        expected_stub_content
    )
