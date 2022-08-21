import io
import pathlib
import pytest

import libcst as cst

from tracing.trace_update import BatchTraceUpdate
from typegen.strats.imports import AddImportTransformer


@pytest.fixture
def importer(scope="function") -> AddImportTransformer:
    batch = BatchTraceUpdate(
        file_name=pathlib.Path("tests", "typegen", "strats", "test_import.py"),
        class_module=None,
        class_name=None,
        function_name="importer",
        line_number=1,
    )

    batch.returns(names2types={"f": ("mycool", "ty")})

    return AddImportTransformer(applicable=batch.to_frame())


@pytest.fixture
def no_future_import() -> tuple[cst.Module, cst.Module]:
    contents = r"""def f(): return 5"""
    expected = r"""from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mycool import ty
def f(): return 5"""

    return cst.parse_module(contents), cst.parse_module(expected)


@pytest.fixture
def existing_future_import() -> tuple[cst.Module, cst.Module]:
    contents = r"""from __future__ import annotations
def f(): return 5"""

    expected = r"""from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mycool import ty
def f(): return 5"""

    return cst.parse_module(contents), cst.parse_module(expected)


@pytest.fixture
def missing_future_import() -> tuple[cst.Module, cst.Module]:
    contents = r"""from __future__ import print_function
def f(): return 5"""
    expected = r"""from __future__ import print_function, annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mycool import ty
def f(): return 5"""

    return cst.parse_module(contents), cst.parse_module(expected)


@pytest.fixture
def multi_future_import() -> tuple[cst.Module, cst.Module]:
    contents = r"""from __future__ import annotations
from __future__ import print_function
def f(): return 5"""

    expected = r"""from __future__ import annotations, print_function
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mycool import ty
def f(): return 5"""

    return cst.parse_module(contents), cst.parse_module(expected)


def test_missing_annotation_import_added(
    importer: AddImportTransformer, no_future_import: tuple[cst.Module, cst.Module]
):
    contents, expected = no_future_import
    output = contents.visit(importer)

    assert expected.code == output.code


def test_existing_annotation_import_retained(
    importer: AddImportTransformer, existing_future_import: tuple[cst.Module, cst.Module]
):
    contents, expected = existing_future_import
    output = contents.visit(importer)

    assert expected.code == output.code


def test_extend_future_import_by_annotation(
    importer: AddImportTransformer, missing_future_import: tuple[cst.Module, cst.Module]
):
    contents, expected = missing_future_import
    output = contents.visit(importer)

    assert expected.code == output.code


def test_future_imports_combined(
    importer: AddImportTransformer, multi_future_import: tuple[cst.Module, cst.Module]
):
    contents, expected = multi_future_import
    output = contents.visit(importer)

    assert expected.code == output.code