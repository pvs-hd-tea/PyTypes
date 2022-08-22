from json import dump
import logging
import pathlib
import typing
import pytest
from unittest import mock

import libcst as cst
import libcst.matchers as m
from libcst.tool import dump

from fetching.projio import Project

from fetching.strat import PyTestStrategy

cwd = pathlib.Path.cwd() / "tests" / "resource" / "sample_decorator_appender_folder"


@pytest.fixture()
def project_folder():
    with mock.patch(
        "fetching.projio.Project.test_directories",
        new_callable=mock.PropertyMock,
    ) as m:
        m.return_value = [cwd]
        p = Project(cwd)

        yield p


class ValidPytestApplicationVisitor(cst.CSTVisitor):
    # import sys
    SYS_IMPORT = m.Import(names=[m.ImportAlias(name=m.Name(value="sys"))])

    # from tracing import decorators
    DECORATOR_IMPORT = m.ImportFrom(
        module=m.Name("tracing"),
        names=[m.ImportAlias(name=m.Name(value="decorators"))],
    )

    # @decorators.trace
    TRACE = m.Decorator(
        decorator=m.Attribute(value=m.Name("decorators"), attr=m.Name("trace"))
    )

    # from __future__ import ...
    _FUTURE_IMPORT_MATCH = m.ImportFrom(module=m.Name(value="__future__"))

    def __init__(self) -> None:
        self.sys_import_exists = False
        self.decorator_import_exists = False
        self.all_tests_are_traced = True

        self.import_found = False
        self.standard_import_from_found = False
        self.test_found = False

        self._has_import_future = False

    def visit_Import(self, node: cst.Import) -> bool | None:
        self.import_found = True
        self.sys_import_exists = self.sys_import_exists or m.matches(
            node, ValidPytestApplicationVisitor.SYS_IMPORT
        )

        logging.debug(f"{self.import_found=}  {self.sys_import_exists=}")
        return True

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        if m.matches(node, ValidPytestApplicationVisitor._FUTURE_IMPORT_MATCH):
            assert not self.import_found, f"Found __future__ import after imports!"

            # No other ImportFroms may have appeared before this 
            assert not self.standard_import_from_found, f"Found __future__ import after other import froms!"
            self._has_import_future = True

        else:
            # This is an import-from that is NOT a from __future__ import
            self.standard_import_from_found = True

        self.decorator_import_exists = self.decorator_import_exists or m.matches(
            node, ValidPytestApplicationVisitor.DECORATOR_IMPORT
        )

        logging.debug(f"{self.standard_import_from_found=}  {self.decorator_import_exists=}")
        return True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        if node.name.value.startswith("test_"):
            self.test_found = True
            self.all_tests_are_traced = self.all_tests_are_traced and any(
                m.matches(d, ValidPytestApplicationVisitor.TRACE)
                for d in node.decorators
            )

        logging.debug(f"{self.test_found=}  {self.all_tests_are_traced=}")
        return True


@pytest.fixture(scope="function")
def recursed_globs() -> typing.Iterator[list[pathlib.Path]]:
    paths = list(cwd.rglob("test_*.py"))
    backups = [file.open().read() for file in paths]

    yield paths

    for backup, file in zip(backups, paths):
        file.open("w").write(backup)


@pytest.fixture(scope="function")
def nonrecursed_globs() -> typing.Iterator[list[pathlib.Path]]:
    paths = list(cwd.glob("test_*.py"))
    backups = [file.open().read() for file in paths]

    yield paths

    for backup, file in zip(backups, paths):
        file.open("w").write(backup)


def check_file_is_valid(filepath: pathlib.Path):
    module = cst.parse_module(filepath.open().read())
    logging.info(f"{module.code}")

    visitor = ValidPytestApplicationVisitor()
    module.visit(visitor)

    assert visitor.import_found, f"No imports found:\n{module.code}"
    assert visitor.sys_import_exists, f"Could not find sys import:\n{module.code}"

    assert visitor.standard_import_from_found, f"No from x import ys found:\n{module.code}"
    assert visitor.decorator_import_exists, f"No decorator import found:\n{module.code}"

    assert visitor.test_found, f"No tests found:\n{module.code}"
    assert visitor.all_tests_are_traced, f"Not all tests are decorated:\n{module.code}"


def test_if_test_object_searches_for_test_files_in_folders_including_subfolders(
    project_folder, recursed_globs
):
    test_object = PyTestStrategy(pathlib.Path.cwd(), recurse_into_subdirs=True)
    test_object.apply(project_folder)

    for test_file_path in recursed_globs:
        assert test_file_path.exists()
        check_file_is_valid(test_file_path)


def test_if_test_object_searches_for_test_files_in_folders_excluding_subfolders(
    project_folder, nonrecursed_globs
):
    test_object = PyTestStrategy(pathlib.Path.cwd(), recurse_into_subdirs=False)
    test_object.apply(project_folder)

    for test_file_path in nonrecursed_globs:
        assert test_file_path.exists()
        check_file_is_valid(test_file_path)


@pytest.fixture
def future_test_project():
    with mock.patch(
        "fetching.projio.Project.test_directories",
        new_callable=mock.PropertyMock,
    ) as m:
        resource_path = pathlib.Path("tests", "resource", "fetching")
        m.return_value = [resource_path]
        p = Project(resource_path)

        yield p


@pytest.fixture
def has_future_import() -> typing.Iterator[pathlib.Path]:
    p = pathlib.Path("tests", "resource", "fetching", "test_has_future_import.py")
    backup = p.open().read()

    yield p

    with p.open("w") as f:
        f.write(backup)


def test_if_future_has_correct_position(
    future_test_project: Project, has_future_import: pathlib.Path
):
    test_object = PyTestStrategy(pathlib.Path.cwd(), recurse_into_subdirs=True)
    test_object.apply(future_test_project)

    assert has_future_import.exists()
    check_file_is_valid(has_future_import)
