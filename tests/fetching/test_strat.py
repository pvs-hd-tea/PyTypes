from json import dump
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
        "fetching.projio.Project.test_directory",
        new_callable=mock.PropertyMock,
    ) as m:
        m.return_value = cwd
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

    def __init__(self) -> None:
        self.sys_import_exists = False
        self.decorator_import_exists = False
        self.all_tests_are_traced = True

        self.import_found = False
        self.import_from_found = False
        self.test_found = False

    def __bool__(self) -> bool:
        return all(
            [
                self.sys_import_exists and self.import_found,
                self.decorator_import_exists and self.import_from_found,
                self.all_tests_are_traced and self.test_found,
            ]
        )

    def visit_Import(self, node: cst.Import) -> bool | None:
        self.import_found = True
        self.sys_import_exists = self.sys_import_exists or m.matches(
            node, ValidPytestApplicationVisitor.SYS_IMPORT
        )
        return True

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        self.import_from_found = True
        self.decorator_import_exists = self.decorator_import_exists or m.matches(
            node, ValidPytestApplicationVisitor.DECORATOR_IMPORT
        )
        return True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        if node.name.value.startswith("test_"):
            self.test_found = True
            self.all_tests_are_traced = self.all_tests_are_traced and any(
                m.matches(d, ValidPytestApplicationVisitor.TRACE)
                for d in node.decorators
            )
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
    visitor = ValidPytestApplicationVisitor()
    module.visit(visitor)

    assert bool(
        visitor
    ), f"At least one of these is false! {visitor.sys_import_exists=}, {visitor.decorator_import_exists=}, {visitor.all_tests_are_traced=}\n"
    f"File: {filepath.open().read()}"


def test_if_test_object_searches_for_test_files_in_folders_including_subfolders_it_overwrites_test_files(
    project_folder, recursed_globs
):
    test_object = PyTestStrategy(pathlib.Path.cwd(), recurse_into_subdirs=True)
    test_object.apply(project_folder)

    for test_file_path in recursed_globs:
        assert test_file_path.exists()
        check_file_is_valid(test_file_path)


def test_if_test_object_searches_for_test_files_in_folders_excluding_subfolders_it_overwrites_test_files(
    project_folder, nonrecursed_globs
):
    test_object = PyTestStrategy(pathlib.Path.cwd(), recurse_into_subdirs=False)
    test_object.apply(project_folder)

    for test_file_path in nonrecursed_globs:
        assert test_file_path.exists()
        check_file_is_valid(test_file_path)
