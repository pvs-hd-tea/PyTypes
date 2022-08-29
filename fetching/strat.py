import enum
import logging
import libcst as cst
import libcst.matchers as m
from abc import ABC, abstractmethod
import pathlib
import re
from re import Pattern

from .projio import Project
import constants
from common.ptconfig import write_config, TomlCfg, PyTypes


class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework;
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test
    functions to be traced upon execution.
    """

    def __init__(self, recurse_into_subdirs: bool = True):
        self.globber = pathlib.Path.rglob if recurse_into_subdirs else pathlib.Path.glob

    def apply(self, project: Project):
        """Apply the subclass-specific strategy to the test files found in the project

        :param project: Path to the fetched resource, now a project
        """
        assert project.test_directory is not None

        for path in filter(
            self._is_test_file, self.globber(project.test_directory, "*")
        ):
            self._apply(path)

        cfg_path = project.root / constants.CONFIG_FILE_NAME
        pts = PyTypes(
            project=project.root.name,
            proj_path=project.root,
            stdlib_path=pathlib.Path("stdlib", "goes", "here"),
            venv_path=pathlib.Path("venv", "goes", "here"),
        )

        toml = TomlCfg(pts, unifier=None)  # type: ignore
        write_config(cfg_path, toml)

    @abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """Perform IO operation to modify the file pointed to by path"""
        pass

    @abstractmethod
    def _is_test_file(self, path: pathlib.Path) -> bool:
        """True iff path is a file / folder that will be executed by the framework"""
        pass


class PyTestStrategy(ApplicationStrategy):
    FUNCTION_PATTERN = constants.PYTEST_FUNCTION_PATTERN

    def __init__(self, pytest_root: pathlib.Path, recurse_into_subdirs: bool = True):
        super().__init__(recurse_into_subdirs)

        self.pytest_root = pytest_root

        self.sys_path_ext_node = cst.Expr(
            cst.parse_expression(f"sys.path.append('{self.pytest_root}')")
        )

    def _apply(self, path: pathlib.Path) -> None:
        # transformer is stateful, meaning it must be reinstantiated
        dec_trans = AppendDecoratorTransformer(
            PyTestStrategy.FUNCTION_PATTERN, self.sys_path_ext_node
        )

        with path.open() as f:
            original = cst.parse_module(f.read())
            updated = original.visit(dec_trans)

        with path.open("w") as f:
            f.write(updated.code)

    def _is_test_file(self, path: pathlib.Path) -> bool:
        if path.name.startswith("test_"):
            return path.name.endswith(".py")

        return path.name.endswith("_test.py")


ADT_LOGGER = logging.getLogger("AppendDecoratorTransformer")


class AppendDecoratorTransformer(cst.CSTTransformer):
    """
    Transforms an AST such that the trace decorator is appended on each test function.
    Additionally, imports are generated in the correct locations so that using
    the decorator is possible
    """

    TRACE_DECORATOR = cst.Decorator(
        decorator=cst.Attribute(value=cst.Name("decorators"), attr=cst.Name("trace"))
    )
    _FUTURE_IMPORT_MATCH = m.ImportFrom(module=m.Name(value="__future__"))

    SYS_IMPORT = cst.Import(names=[cst.ImportAlias(name=cst.Name("sys"))])
    PYTYPE_IMPORT = cst.ImportFrom(
        module=cst.Name("tracing"), names=[cst.ImportAlias(name=cst.Name("decorators"))]
    )

    class State(enum.IntEnum):
        # No preamble has been generated, and no
        # viable preamble insertion point has been found
        INITIAL = 0

        # A fitting preamble insertion point has been found
        INSERTION_POINT_FOUND = 1

        # The preamble has been added to the AST
        PREAMBLE_GENERATED = 2

    def __init__(
        self,
        test_function_name_pattern: Pattern[str],
        sys_path_ext: cst.BaseSmallStatement,
    ):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern
        self._sys_path_ext = sys_path_ext
        self._state: AppendDecoratorTransformer.State = (
            AppendDecoratorTransformer.State.INITIAL
        )

    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        # If there are no imports, then the state may not change completely
        if self._state != AppendDecoratorTransformer.State.PREAMBLE_GENERATED:
            ADT_LOGGER.debug("Preamble has not yet been added, adding at fallthru")
            # Generate missing imports at the top
            changes = cst.SimpleStatementLine(
                [
                    AppendDecoratorTransformer.SYS_IMPORT,
                    self._sys_path_ext,
                    AppendDecoratorTransformer.PYTYPE_IMPORT,
                ]
            )
            new_body = list(updated_node.body)
            new_body.insert(0, changes)

            self._state = AppendDecoratorTransformer.State.PREAMBLE_GENERATED
            return updated_node.with_changes(body=new_body)

        return updated_node

    def leave_Import(
        self, _: cst.Import, updated_node: cst.Import
    ) -> cst.BaseSmallStatement | cst.FlattenSentinel[cst.BaseSmallStatement]:
        if self._state != AppendDecoratorTransformer.State.PREAMBLE_GENERATED:
            ADT_LOGGER.debug("Adding preamble after Import")
            self._state = AppendDecoratorTransformer.State.PREAMBLE_GENERATED
            return cst.FlattenSentinel(
                [
                    updated_node,
                    AppendDecoratorTransformer.SYS_IMPORT,
                    self._sys_path_ext,
                    AppendDecoratorTransformer.PYTYPE_IMPORT,
                ]
            )

        return updated_node

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        if self._state == AppendDecoratorTransformer.State.INITIAL:
            if m.matches(node, AppendDecoratorTransformer._FUTURE_IMPORT_MATCH):
                ADT_LOGGER.debug(
                    "Detected from __future__ import ..., continuing search for insertion point"
                )

            else:
                ADT_LOGGER.debug("ImportFrom detected that is unrelated to __future__")
                self._state = AppendDecoratorTransformer.State.INSERTION_POINT_FOUND

        return True

    def leave_ImportFrom(
        self, _: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement] | cst.BaseSmallStatement:
        if self._state == AppendDecoratorTransformer.State.INSERTION_POINT_FOUND:
            ADT_LOGGER.debug("Adding preamble after ImportFrom")
            self._state = AppendDecoratorTransformer.State.PREAMBLE_GENERATED
            return cst.FlattenSentinel(
                [
                    updated_node,
                    AppendDecoratorTransformer.SYS_IMPORT,
                    self._sys_path_ext,
                    AppendDecoratorTransformer.PYTYPE_IMPORT,
                ]
            )

        return updated_node

    def leave_ClassDef(
        self, _: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.BaseStatement | cst.FlattenSentinel[cst.BaseStatement]:
        if self._state != AppendDecoratorTransformer.State.PREAMBLE_GENERATED:
            self._state = AppendDecoratorTransformer.State.PREAMBLE_GENERATED
            return cst.FlattenSentinel(
                [
                    cst.SimpleStatementLine(
                        [
                            AppendDecoratorTransformer.SYS_IMPORT,
                            self._sys_path_ext,
                            AppendDecoratorTransformer.PYTYPE_IMPORT,
                        ]
                    ),
                    updated_node,
                ]
            )

        return updated_node

    def leave_FunctionDef(
        self, _: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FlattenSentinel[cst.BaseStatement] | cst.FunctionDef:
        if re.match(self.test_function_name_pattern, updated_node.name.value):
            ADT_LOGGER.debug(f"Adding decorator to {updated_node.name.value}")
            updated_node = updated_node.with_changes(
                decorators=(
                    *updated_node.decorators,
                    AppendDecoratorTransformer.TRACE_DECORATOR,
                )
            )

        else:
            ADT_LOGGER.debug(f"Skipping adding decorator to {updated_node.name.value}")

        if self._state != AppendDecoratorTransformer.State.PREAMBLE_GENERATED:
            self._state = AppendDecoratorTransformer.State.PREAMBLE_GENERATED
            return cst.FlattenSentinel(
                [
                    cst.SimpleStatementLine(
                        [
                            AppendDecoratorTransformer.SYS_IMPORT,
                            self._sys_path_ext,
                            AppendDecoratorTransformer.PYTYPE_IMPORT,
                        ]
                    ),
                    updated_node,
                ]
            )

        return updated_node
